"""模块功能：编排自动补给判断和快速补给面板操作。

上层调用：
- main_page.page：在编队调整完成后调用 apply_supply。

下层依赖：
- main_page.page：提供面板和舰船槽位点击。
- supply.recognition：识别自动补给开关。
- supply.constants：提供补给按钮和同步参数。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.fleet.support.supply import constants, recognition
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Sequence

    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.application.ui.controller.fleet.main_page import BattlePreparationPage


_log = get_logger('ui.fleet.support.supply')


def apply_supply(
    ctx: UIContext,
    page: BattlePreparationPage,
    ship_ids: Sequence[int] | None = None,
) -> None:
    """自动补给关闭时打开快速补给并补给指定槽位。"""
    if recognition.check_auto_supply_enabled(ctx.ctrl.screenshot()):
        return
    supply(page, ship_ids)


def supply(
    page: BattlePreparationPage,
    ship_ids: Sequence[int] | None = None,
) -> None:
    """打开快速补给面板并点击指定物理舰船槽位。"""
    if ship_ids is None:
        ship_ids = range(6)
    open_quick_supply(page)
    time.sleep(constants.SUPPLY_PANEL_WAIT)
    for slot in ship_ids:
        if slot not in range(6):
            _log.warning('[UI] 无效补给槽位: {}', slot)
            continue
        page.click_ship_slot(slot)
        time.sleep(constants.SUPPLY_SLOT_WAIT)


def switch_auto_supply(ctx: UIContext) -> None:
    """点击自动补给开关。"""
    _log.debug('[UI] 出征准备 -> 切换自动补给')
    ctx.ctrl.click(*constants.CLICK_AUTO_SUPPLY)


def open_quick_supply(page: BattlePreparationPage) -> None:
    """打开准备页快速补给面板。"""
    from autowsgr.application.ui.controller.fleet.main_page import Panel

    page.select_panel(Panel.QUICK_SUPPLY)


__all__ = ['apply_supply', 'open_quick_supply', 'supply', 'switch_auto_supply']
