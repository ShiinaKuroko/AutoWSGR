"""决战旧编队入口的兼容壳。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.pages.battle_preparation.fleet_change import decisive as _decisive


change_decisive_fleet = _decisive.change_decisive_fleet
time = _decisive.time


if TYPE_CHECKING:
    from collections.abc import Sequence

    from autowsgr.application.ui.pages.decisive.preparation import DecisiveBattlePreparationPage


def change_fleet_legacy(
    page: DecisiveBattlePreparationPage,
    fleet_id: int | None,
    ship_names: Sequence[str | None],
) -> bool:
    """保留旧调用签名，实际委托统一决战编队分支。"""
    names = list(ship_names)
    if fleet_id == 1 and (not names or not names[0]):
        raise ValueError('1 队槽位 0 不能为空')
    if fleet_id and page.get_selected_fleet(page._ctrl.screenshot()) != fleet_id:
        page.select_fleet(fleet_id)
        time.sleep(0.5)
    return change_decisive_fleet(page, names)


__all__ = ['change_fleet_legacy']
