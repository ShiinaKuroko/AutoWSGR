"""模块功能：在军阶室二级页执行退回上一级与进入技能列表。

上层调用：
- application.ui.navigation：执行军阶室回后院主页的页面边动作。
- business：进入军阶室技能列表（三级页，尚未接入导航图）。

下层依赖：
- application.ui.controller.backyard.main_page.constants：提供退回与三级页入口落点。

边界：只点击退回按钮与三级页入口，不识别画面、不确认终态、不编排军阶业务。
三级页（技能列表）功能后续开发，本模块只提供进入它的点击。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.backyard.main_page import constants
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui.backyard.rank_room_page')


# ── 页面控制器 ──────────────────────────────────────────────────────────────


class RankRoomPage:
    """军阶室二级页的单击控制器。"""

    def __init__(self, ctx: ContextHandle) -> None:
        """绑定任务上下文。

        Args:
            ctx: 提供设备服务的 dispatch 上下文句柄。
        """
        self._ctx = ctx

    # ── 进入三级页 ──────────────────────────────────────────────────────────

    def go_to_skill_list(self) -> None:
        """点击技能列表入口，进入三级页。

        三级页尚未接入导航图，本方法只负责点击。
        """
        _log.info('[UI] 军阶室 → 技能列表：position={!r}', constants.CLICK_RANK_SKILL_LIST)
        self._ctx.runtime.ctrl.click(*constants.CLICK_RANK_SKILL_LIST)

    # ── 返回 ────────────────────────────────────────────────────────────────

    def go_home(self) -> None:
        """点击通用回首页按钮，直接回主页面。"""
        _log.info('[UI] 军阶室 → 回首页：position={!r}', constants.CLICK_HOME)
        self._ctx.runtime.ctrl.click(*constants.CLICK_HOME)

    def go_back(self) -> None:
        """点击退回按钮，回后院主页。"""
        _log.info('[UI] 军阶室 → 退回后院主页：position={!r}', constants.CLICK_BACK)
        self._ctx.runtime.ctrl.click(*constants.CLICK_BACK)


__all__ = ['RankRoomPage']
