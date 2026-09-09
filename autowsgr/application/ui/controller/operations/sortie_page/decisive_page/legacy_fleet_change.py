"""模块功能：保留决战旧编队入口并委托当前统一编队分支。

上层调用：
- application.ui.controller.operations.sortie_page.decisive_page.preparation_page：在关闭新算法时调用旧入口。
- testing.ui：验证旧决战编队分支。

下层依赖：
- application.ui.controller.battle_preparation.fleet_change.decisive：执行统一决战编队。

本模块只保留已有调用契约，不复制选船实现或增加新的兼容路径。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.battle_preparation.fleet_change import decisive as _decisive


change_decisive_fleet = _decisive.change_decisive_fleet
time = _decisive.time


if TYPE_CHECKING:
    from collections.abc import Sequence

    from autowsgr.application.ui.controller.operations.sortie_page.decisive_page.preparation_page import (
        DecisiveBattlePreparationPage,
    )


def change_fleet_legacy(
    page: DecisiveBattlePreparationPage,
    fleet_id: int | None,
    ship_names: Sequence[str | None],
) -> bool:
    """保留旧调用签名并委托统一决战编队分支。

    Args:
        page: 决战出征准备页控制器。
        fleet_id: 要操作的舰队编号；没有指定时保持当前舰队。
        ship_names: 按槽位排列的目标舰船名称。

    Returns:
        编队成功时返回 ``True``，否则返回 ``False``。
    """
    names = list(ship_names)
    if fleet_id == 1 and (not names or not names[0]):
        raise ValueError('1 队槽位 0 不能为空')
    if fleet_id and page.read_selected_fleet(page._ctrl.screenshot()) != fleet_id:
        page.select_fleet(fleet_id)
        time.sleep(0.5)
    return change_decisive_fleet(page, names)


__all__ = ['change_fleet_legacy']
