"""模块功能：在餐厅二级页执行回首页与退回上一级。

上层调用：
- application.ui.navigation：执行该页回主页面与退回后院主页的页面边动作。

下层依赖：
- application.ui.controller.backyard.main_page.constants：提供二级页按钮落点。

边界：只点击返回按钮，不识别画面、不确认终态、不编排餐厅二级页业务。
餐厅的做饭业务尚未迁移到新链路，等第二阶段移植后再补回本模块。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.backyard.main_page import constants
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui.backyard.canteen_page')


# ── 页面控制器 ──────────────────────────────────────────────────────────────


class CanteenPage:
    """餐厅二级页的单击控制器。"""

    def __init__(self, ctx: ContextHandle) -> None:
        """绑定任务上下文。

        Args:
            ctx: 提供设备服务的 dispatch 上下文句柄。
        """
        self._ctx = ctx

    # ── 返回 ────────────────────────────────────────────────────────────────

    def go_home(self) -> None:
        """点击通用回首页按钮，直接回主页面。"""
        _log.info('[UI] 餐厅二级页 → 回首页：position={!r}', constants.CLICK_HOME)
        self._ctx.runtime.ctrl.click(*constants.CLICK_HOME)

    def go_back(self) -> None:
        """点击退回按钮，回后院主页。"""
        _log.info('[UI] 餐厅二级页 → 退回后院主页：position={!r}', constants.CLICK_BACK)
        self._ctx.runtime.ctrl.click(*constants.CLICK_BACK)


__all__ = ['CanteenPage']
