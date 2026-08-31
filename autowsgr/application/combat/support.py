"""战斗准备阶段的公共支援操作。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.pages.battle_preparation import BattlePreparationPage
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from autowsgr.application.runtime import RuntimeContext as GameContext


_log = get_logger('combat')


def ensure_battle_support(ctx: GameContext, *, enabled: bool = True) -> None:
    """确保军阶战役支援开关处于目标状态。"""
    page = BattlePreparationPage(ctx)
    screen = ctx.ctrl.screenshot()
    if page.is_support_enabled(screen) == enabled:
        _log.debug('[Combat] 战役支援已为目标状态 {}', enabled)
        return
    _log.info('[Combat] 战役支援状态不符，切换为 {}', enabled)
    page.toggle_battle_support()
    time.sleep(0.5)
