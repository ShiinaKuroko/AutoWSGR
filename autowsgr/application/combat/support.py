"""战斗准备阶段的公共支援操作。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.fleet import BattlePreparationPage


if TYPE_CHECKING:
    from autowsgr.application.runtime import RuntimeContext as GameContext


def ensure_battle_support(ctx: GameContext, *, enabled: bool = True) -> None:
    """确保军阶战役支援开关处于目标状态。"""
    page = BattlePreparationPage(ctx)
    page.ensure_campaign_support(enabled=enabled)
