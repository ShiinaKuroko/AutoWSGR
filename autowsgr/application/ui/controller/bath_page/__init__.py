"""浴室页面 UI 模块。

公开 API::

    from autowsgr.application.ui.controller.bath_page import BathPage, RepairShipInfo
"""

from .page import (
    BathPage,
    RepairShipInfo,
)
from .recognition import recognize_repair_cards


__all__ = [
    'BathPage',
    'RepairShipInfo',
    'recognize_repair_cards',
]
