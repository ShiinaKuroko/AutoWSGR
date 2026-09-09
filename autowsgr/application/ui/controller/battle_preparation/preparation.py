"""模块功能：组合出征准备页面的基础、检测、补给、维修和编队操作能力。

上层调用：
- application.ui.navigation：注册出征准备页面检查器并执行页面回退。
- business.combat：执行普通、战役、演习和活动出征准备。
- business.combat.decisive：复用准备页的舰队、补给和维修能力。
- testing.ui、testing.business：验证页面操作和选船调用链。

下层依赖：
- application.ui.controller.battle_preparation.base：提供页面原子操作。
- application.ui.controller.battle_preparation.detection：提供舰队状态检测。
- application.ui.controller.battle_preparation.fleet_change：提供编队调整。
- application.ui.controller.battle_preparation.repair、supply：提供修理和补给动作。

本模块只负责组合页面能力；选船实现仍保留在 `fleet_change/` 原目录，OCR 生命周期
问题不在此处处理。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.battle_preparation.base import (
    CLICK_PANEL,
    PANEL_PROBE,
    BaseBattlePreparation,
    Panel,
    RepairStrategy,
)
from autowsgr.application.ui.controller.battle_preparation.constants import PAGE_SIGNATURE
from autowsgr.application.ui.controller.battle_preparation.detection import (
    DetectionMixin,
    FleetInfo,
)
from autowsgr.application.ui.controller.battle_preparation.fleet_change import (
    CampaignFleetChangeMixin,
)
from autowsgr.application.ui.controller.battle_preparation.repair import RepairMixin
from autowsgr.application.ui.controller.battle_preparation.supply import SupplyMixin


__all__ = [
    'CLICK_PANEL',
    'PAGE_SIGNATURE',
    'PANEL_PROBE',
    'BattlePreparationPage',
    'FleetInfo',
    'Panel',
    'RepairStrategy',
]


class BattlePreparationPage(
    DetectionMixin,
    SupplyMixin,
    RepairMixin,
    CampaignFleetChangeMixin,
    BaseBattlePreparation,
):
    """出征准备页面控制器。

    聚合所有 Mixin 能力:

    - **检测** (:class:`DetectionMixin`):
      ``detect_ship_damage``, ``detect_fleet_info``
    - **补给/支援** (:class:`SupplyMixin`):
      ``supply``, ``apply_supply``, ``toggle_battle_support``, ``check_support_enabled``
    - **修理** (:class:`RepairMixin`):
      ``repair_slots``, ``apply_repair``
    - **换船** (:class:`CampaignFleetChangeMixin`):
      ``change_fleet``
    - **基础** (:class:`BaseBattlePreparation`):
      ``go_back``, ``start_battle``, ``select_fleet``, ``select_panel`` 等
    """

    # FleetInfo 作为类属性保留，供既有调用方使用 BattlePreparationPage.FleetInfo。
    FleetInfo = FleetInfo
