"""出征准备页面 UI 控制器。

最终控制器类 :class:`BattlePreparationPage` 通过菱形继承聚合所有 Mixin:

继承结构::

    BaseBattlePreparation
    ├── DetectionMixin        (血量 / 等级识别)
    ├── SupplyMixin           (补给 / 支援)
    ├── RepairMixin           (修理, 依赖 DetectionMixin)
    └── CampaignFleetChangeMixin (按 task_type 选择战役或通用流程)
        └── FleetChangeMixin     (普通/活动/演习/决战换船)
        └── FleetAlignmentMixin  (成员更换与位置调整)
            └── FleetSelectionMixin  (船池选择页面操作)
                └── FleetPlanningMixin  (目标分配与槽位规划)
                    └── FleetRuleMixin  (舰队规则匹配与校验)
                        └── FleetDetectMixin  (准备页舰队 OCR 检测)
            ↓
    BattlePreparationPage     (最终控制器)

校准数据来自 :mod:`autowsgr.common.calibration.battle_preparation`。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.battle_preparation.base import (
    CLICK_PANEL,
    PAGE_SIGNATURE,
    PANEL_PROBE,
    BaseBattlePreparation,
    Panel,
    RepairStrategy,
)
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
      ``supply``, ``apply_supply``, ``toggle_battle_support``, ``is_support_enabled``
    - **修理** (:class:`RepairMixin`):
      ``repair_slots``, ``apply_repair``
    - **换船** (:class:`CampaignFleetChangeMixin`):
      ``change_fleet``
    - **基础** (:class:`BaseBattlePreparation`):
      ``go_back``, ``start_battle``, ``select_fleet``, ``select_panel`` 等
    """

    # FleetInfo 挂在类上方便外部引用: BattlePreparationPage.FleetInfo
    FleetInfo = FleetInfo
