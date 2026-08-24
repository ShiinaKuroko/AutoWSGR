"""兼容 shim — 实现已迁移至 :mod:`autowsgr.infra.base.ui.pages.bath_page`。

老代码仍可 ``from autowsgr.ui.bath_page import BathPage``，
新代码请直接使用新路径。
"""

from autowsgr.infra.base.ui.pages.bath_page import (
    CHOOSE_REPAIR_OVERLAY_SIGNATURE,
    PAGE_SIGNATURE,
    BathPage,
    RepairShipInfo,
    recognize_repair_cards,
)

__all__ = [
    'CHOOSE_REPAIR_OVERLAY_SIGNATURE',
    'PAGE_SIGNATURE',
    'BathPage',
    'RepairShipInfo',
    'recognize_repair_cards',
]
