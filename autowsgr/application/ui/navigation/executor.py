"""模块功能：按路径逐边执行导航，并在每跳两端做前后识别。

上层调用：
- application.ui.navigation.service：把算好的路径交给执行器走出去。

下层依赖：
- navigation.registry：查询页面的到达确认入口。
- navigation.types：页面契约与导航错误。
- dispatch.session：进程级导航栈。

边界：只执行「已经算好的路径」；不算路、不做入口判断、不处理每日浮窗。
传了 tab 参数时，最后一跳改用该标签的 checker 做到达确认（见 §标签）。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation import registry
from autowsgr.application.ui.navigation.types import NavigationError, PageName
from autowsgr.common.system.logger import get_logger


_log = get_logger('ui.navigation.executor')


# 覆盖层页面：每日三个浮窗。它们盖在底层页面上，不参与「我在哪一页」的探测。
_OVERLAY_PAGES = frozenset({PageName.HOME_NEWS, PageName.HOME_REWARD, PageName.HOME_REWARD_CONFIRM})


# ── 页面内标签参数 ──────────────────────────────────────────────────────────

# 点页面入口后页面本身还在切换动画里，此时点标签会落空；先等它稳定再点、再验。
_TAB_SETTLE_SECONDS = 2.0


if TYPE_CHECKING:
    from autowsgr.application.ui.navigation.types import NavTarget
    from autowsgr.dispatch.context import ContextHandle
    from autowsgr.dispatch.session import SessionState


class NavigationExecutor:
    """逐边执行一条导航路径，并在每跳两端自动做前后识别。

    一次点击的语义天然是成对的：旧页面的标志应当消失（后识别），新页面的标志应当
    出现（前识别）。执行器同时掌握「离开谁」（压栈前的栈顶）与「去往谁」
    （边的目标），因此这个判断由它统一负责，边与 checker 都不需要各自声明。

    Args:
        ctx: 提供设备服务与截图事实的 dispatch 上下文句柄。
        session: 进程级导航会话状态。
    """

    def __init__(self, ctx: ContextHandle, session: SessionState) -> None:
        """绑定任务上下文与导航会话状态。"""
        self._ctx = ctx
        self._session = session

    # ── 两个方向 ────────────────────────────────────────────────────────────

    def walk_forward(self, path: tuple[NavTarget, ...], params: dict[str, object]) -> None:
        """前进：按路径从当前页走向目标页。

        每跳依次执行：边的动作 → 到达确认，最后把目标页压进导航栈。

        Args:
            path: 已经算好的路径。
            params: 透传给边动作的参数（例如活动章节的 node、区服的 position）。

        Raises:
            NavigationError: 到达确认失败。
        """
        # 标签优先取调用方参数，其次取边自己声明的（如「首页 → 出征页」固定切回出征）。
        requested = params.get('tab')
        tab = requested if isinstance(requested, str) else None
        if tab is None and len(path) == 1 and path[0].tab is not None:
            tab = path[0].tab
        for index, edge in enumerate(path):
            _log.debug('[UI] 导航执行 → 前进：edge={!r}', edge.description)
            edge.action(self._ctx, **params)
            # 标签只落在最后一跳：中间跳的目标页面没有这个标签，也不该切。
            if tab is not None and index == len(path) - 1:
                self._enter_tab(edge.target, tab)
            else:
                self._confirm_arrival(edge)
            self._session.push_page(edge.target.value)

    def walk_backward(self, path: tuple[NavTarget, ...]) -> None:
        """后退：按路径从当前页退回上一页。

        与前进的差别只有两点：回退不接受调用方参数；栈的记账由调用方完成
        （`navigate_back` 已经弹掉一层），这里只走路径、点、确认，不再动栈。
        回退一个「锚点」跟路径上有几步无关，所以不能按步数记账。

        Args:
            path: 已经算好的回退路径。

        Raises:
            NavigationError: 到达确认失败。
        """
        for edge in path:
            _log.debug('[UI] 导航执行 → 后退：edge={!r}', edge.description)
            edge.action(self._ctx)
            self._confirm_arrival(edge)

    # ── 页面层识别 ──────────────────────────────────────────────────────────

    def detect_layer(self) -> PageName | None:
        """返回当前最上面那一层：按页面深度降序扫一遍，命中即停。

        覆盖层（浮窗、侧边栏、二级菜单）总是比被盖住的页面更深，因此排在最前的
        命中者就是当前层——不需要任何页面去「排除」别的页面。
        每个入口只看当前一帧；等待页面切换由调用方决定。

        Returns:
            当前层；一个确认入口都没命中时为 None。
        """
        # 浮窗是覆盖层：问「我在哪一页」问的是底层页面，把浮窗排除在外，
        # 否则「处理过的浮窗直接放行」会把当前页认成浮窗，路径就从错的起点算。
        by_depth = sorted(
            (
                page
                for page in PageName
                if registry.get_checker(page) is not None and page not in _OVERLAY_PAGES
            ),
            key=registry.depth_of,
            reverse=True,
        )
        for page in by_depth:
            confirm = registry.get_checker(page)
            if confirm is None:
                continue
            try:
                matched = confirm(self._ctx, attempts=1, interval_seconds=0.2)
            except Exception:
                # 某些入口需要任务额外提供上下文（如活动玩法），探测时没有，
                # 报错就当它不匹配，继续看下一层。
                matched = False
            if matched:
                return page
        return None

    def _enter_tab(self, page: PageName, tab: str) -> None:
        """切到目标页内的标签，并用该标签自己的 checker 确认。

        传了标签时页面级确认不参与：切到别的标签之后，认"默认标签激活"的页面级
        checker 本来就该失败，两者互斥。

        Args:
            page: 刚到达的页面。
            tab: 标签键，见 `registry.get_tabs`。

        Raises:
            NavigationError: 页面没有该标签，或点完标签仍未激活。
        """
        entry = registry.get_tabs(page).get(tab)
        if entry is None:
            raise NavigationError(f'到达确认失败：{page.value!r} 没有标签 {tab!r}')
        time.sleep(_TAB_SETTLE_SECONDS)
        entry.click(self._ctx)
        if not entry.checker(self._ctx):
            raise NavigationError(f'标签切换失败：{page.value!r} → {entry.description!r}')
        _log.debug(
            '[UI] 导航执行 → 标签确认：page={!r}，tab={!r}，结果=成功',
            page.value,
            entry.description,
        )

    def _confirm_arrival(self, edge: NavTarget) -> None:
        """到达确认：目标页出现，且它确实在最上面。

        目标页的识别入口自带重试（最终透传到 common.vision 的轮询），负责等切换完成；
        随后按页面深度扫一遍，确认没有别的覆盖层还盖在目标页上面。

        Args:
            edge: 刚执行完的边。

        Raises:
            NavigationError: 目标页没出现，或当前层不是目标页。
        """
        confirm = registry.get_checker(edge.target)
        if confirm is None or not edge.confirm:
            _log.debug('[UI] 导航执行 → 到达确认：page={!r}，结果=跳过', edge.target.value)
            return
        # 先等目标页出现（它的入口自带重试，负责等切换动画走完）。
        if not confirm(self._ctx):
            raise NavigationError(f'到达确认失败：{edge.description!r}')
        # 再确认「当前层就是目标」：目标出现不代表它就在最上面——浮窗、侧边栏
        # 这类覆盖层会盖住它，按深度降序扫一遍就能分辨出真正的当前层。
        layer = self.detect_layer()
        if layer is not None and layer is not edge.target:
            raise NavigationError(f'到达确认失败：{edge.description!r}，当前层是 {layer.value!r}')
        _log.debug('[UI] 导航执行 → 到达确认：page={!r}，结果=成功', edge.target.value)


__all__ = ['NavigationExecutor']
