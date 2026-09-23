"""后勤领域类型。"""

from __future__ import annotations

from autowsgr.common.system.enums import IntEnum


class ShipDamageState(IntEnum):
    """舰船血量状态。"""

    NORMAL = 0
    MODERATE = 1
    SEVERE = 2
    NO_SHIP = -1


class RepairMode(IntEnum):
    """修理策略。"""

    moderate_damage = 1
    severe_damage = 2
    repairing = 3


class DestroyShipWorkMode(IntEnum):
    """拆解工作模式。"""

    disable = 0
    include = 1
    exclude = 2
