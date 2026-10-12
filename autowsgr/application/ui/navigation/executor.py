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

        每跳依次执行：边的动作 → 离开确认（后识别）→ 到达确认（前识别），
        最后把目标页压进导航栈。

        Args:
            path: 已经算好的路径。
            params: 透传给边动作的参数（例如活动章节的 node、区服的 position）。

        Raises:
            NavigationError: 离开确认或到达确认失败。
        """
        tab = params.get('tab') if isinstance(params.get('tab'), str) else None
        for index, edge in enumerate(path):
            _log.debug('[UI] 导航执行 → 前进：edge={!r}', edge.description)
            edge.action(self._ctx, **params)
            self._confirm_departure()
            # 标签只落在最后一跳：中间跳的目标页面没有这个标签，也不该切。
            if tab is not None and index == len(path) - 1:
                self._enter_tab(edge.target, tab)
            else:
                self._confirm_arrival(edge)
            self._session.push_page(edge.target.value)

    def walk_backward(self, path: tuple[NavTarget, ...]) -> None:
        """后退：按路径从当前页退回上一页。

        与前进的差别只有两点：回退不接受调用方参数；栈由调用方先退一格，这里把
        走到的页面重新压回去。

        Args:
            path: 已经算好的回退路径。

        Raises:
            NavigationError: 离开确认或到达确认失败。
        """
        for edge in path:
            _log.debug('[UI] 导航执行 → 后退：edge={!r}', edge.description)
            edge.action(self._ctx)
            self._confirm_departure()
            self._confirm_arrival(edge)
            self._session.push_page(edge.target.value)

    # ── 前后识别 ────────────────────────────────────────────────────────────

    def _confirm_departure(self) -> None:
        """离开确认：用后识别确认刚离开的那一页标志已经消失。

        此刻目标页还没压栈，所以栈顶就是出发页。识别节奏由该页在注册表里的确认入口
        自己带（最终透传到 common.vision 的轮询），这里只决定用哪一种识别。
        没有确认入口的页面直接放行。

        Raises:
            NavigationError: 后识别未通过。
        """
        current = self._session.current_page()
        if current is None:
            return
        page = PageName(current)
        confirm = registry.get_checker(page)
        if confirm is None:
            _log.debug('[UI] 导航执行 → 离开确认：page={!r}，结果=跳过', page.value)
            return
        if not confirm(self._ctx, absent=True):
            raise NavigationError(f'离开确认失败：{page.value} 仍然存在')
        _log.debug('[UI] 导航执行 → 离开确认：page={!r}，结果=成功', page.value)

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
            raise NavigationError(
                f'标签切换失败：{page.value!r} → {entry.description!r}'
            )
        _log.debug(
            '[UI] 导航执行 → 标签确认：page={!r}，tab={!r}，结果=成功',
            page.value,
            entry.description,
        )

    def _confirm_arrival(self, edge: NavTarget) -> None:
        """到达确认：用前识别确认目标页标志已经出现。

        Raises:
            NavigationError: 前识别未通过。
        """
        confirm = registry.get_checker(edge.target)
        if confirm is None or not edge.confirm:
            _log.debug('[UI] 导航执行 → 到达确认：page={!r}，结果=跳过', edge.target.value)
            return
        if not confirm(self._ctx):
            raise NavigationError(f'到达确认失败：{edge.description!r}')
        _log.debug('[UI] 导航执行 → 到达确认：page={!r}，结果=成功', edge.target.value)


__all__ = ['NavigationExecutor']
