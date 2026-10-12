"""模块功能：在好友页面执行返回。

上层调用：
- application.ui.navigation：执行好友页面返回主页的页面边动作。

下层依赖：
- application.ui.controller.sidebar.friend_page.constants：提供返回落点。

边界：只点击返回按钮，不识别画面、不确认终态、不涉及好友业务。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.sidebar.friend_page import constants
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui.sidebar.friend_page')


# ── 页面控制器 ──────────────────────────────────────────────────────────────


class FriendPage:
    """好友页面的单击控制器。"""

    def __init__(self, ctx: ContextHandle) -> None:
        """绑定任务上下文。

        Args:
            ctx: 提供设备服务的 dispatch 上下文句柄。
        """
        self._ctx = ctx

    # ── 返回 ────────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击左上角返回按钮，离开好友页面。"""
        _log.info('[UI] 好友 → 返回：position={!r}', constants.CLICK_BACK)
        self._ctx.runtime.ctrl.click(*constants.CLICK_BACK)


__all__ = ['FriendPage']
