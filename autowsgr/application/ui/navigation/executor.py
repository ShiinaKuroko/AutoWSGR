"""模块功能：按路径逐边执行导航，并在每跳两端做前后识别。

上层调用：
- application.ui.navigation.service：把算好的路径交给执行器走出去。

下层依赖：
- navigation.registry：查询页面的到达确认入口。
- navigation.types：页面契约与导航错误。
- dispatch.session：进程级导航栈。

边界：只执行「已经算好的路径」；不算路、不做入口判断、不处理每日浮窗。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation import registry
from autowsgr.application.ui.navigation.types import NavigationError, PageName
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.application.ui.navigation.types import NavTarget
    from autowsgr.dispatch.context import ContextHandle
    from autowsgr.dispatch.session import SessionState


_log = get_logger('ui.navigation.executor')


# 动作之后确认「旧标志消失」「新标志出现」的轮询次数与间隔，单位为秒。
# 个别页面的确认入口自带更长节奏（如首页等登录动画），会先于这两个上限返回。
_CONFIRM_ATTEMPTS = 6
_CONFIRM_INTERVAL_SECONDS = 0.5


class NavigationExecutor:
    """逐边执行一条导航路径，并在每跳两端自动做前后识别。

    一次点击的语义天然是成对的：旧页面的标志应当消失（后识别），新页面的标志应当
    出现（前识别）。执行器同时掌握「离开谁」（压栈前的栈顶）与「去往谁」
    （边的目标），因此这个判断由它统一负责，边与 checker 都不需要各自声明。

    Args:
        ctx: 提供设备服务与截图事实的 dispatch 上下文句柄。
        session: 进程级导航会话状态。
        on_arrive: 到达某页后、确认到达前要做的上层处理（例如到达首页时清每日浮窗）。
    """

    def __init__(
        self,
        ctx: ContextHandle,
        session: SessionState,
        *,
        on_arrive: Callable[[PageName], None] | None = None,
    ) -> None:
        self._ctx = ctx
        self._session = session
        self._on_arrive = on_arrive

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
        for edge in path:
            edge.action(self._ctx, **params)
            self._confirm_departure()
            if self._on_arrive is not None:
                self._on_arrive(edge.target)
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
            edge.action(self._ctx)
            self._confirm_departure()
            if self._on_arrive is not None:
                self._on_arrive(edge.target)
            self._confirm_arrival(edge)
            self._session.push_page(edge.target.value)

    # ── 前后识别 ────────────────────────────────────────────────────────────

    def _confirm_departure(self) -> None:
        """离开确认（后识别）：轮询确认刚离开的那一页标志已经消失。

        此刻目标页还没压栈，所以栈顶就是出发页。没有确认入口的页面直接放行。

        Raises:
            NavigationError: 轮询结束标志仍然存在。
        """
        current = self._session.current_page()
        if current is None:
            return
        page = PageName(current)
        confirm = registry.get_checker(page)
        if confirm is None:
            return
        if self._wait_until_absent(page, confirm):
            return
        raise NavigationError(f'离开确认失败：{page.value} 仍然存在')

    def _confirm_arrival(self, edge: NavTarget) -> None:
        """到达确认（前识别）：轮询确认目标页标志已经出现。

        Raises:
            NavigationError: 轮询结束标志仍未出现。
        """
        confirm = registry.get_checker(edge.target)
        if confirm is None:
            return
        if self._wait_until_present(edge.target, confirm):
            return
        raise NavigationError(f'到达确认失败：{edge.description!r}')

    # ── 轮询 ────────────────────────────────────────────────────────────────

    def _wait_until_present(self, page: PageName, confirm: object) -> bool:
        """轮询等待页面标志出现。"""
        for _ in range(_CONFIRM_ATTEMPTS):
            if confirm(self._ctx):  # type: ignore[operator]
                return True
            time.sleep(_CONFIRM_INTERVAL_SECONDS)
        _log.warning('[UI] 导航确认 → 未出现：page={!r}', page.value)
        return False

    def _wait_until_absent(self, page: PageName, confirm: object) -> bool:
        """轮询等待页面标志消失。"""
        for _ in range(_CONFIRM_ATTEMPTS):
            if not confirm(self._ctx):  # type: ignore[operator]
                return True
            time.sleep(_CONFIRM_INTERVAL_SECONDS)
        _log.warning('[UI] 导航确认 → 未消失：page={!r}', page.value)
        return False


__all__ = ['NavigationExecutor']
