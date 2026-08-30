"""面板 Mixin 子包。"""

from autowsgr.application.ui.pages.map.panels.campaign import CampaignPanelMixin
from autowsgr.application.ui.pages.map.panels.decisive import DecisivePanelMixin
from autowsgr.application.ui.pages.map.panels.exercise import ExercisePanelMixin
from autowsgr.application.ui.pages.map.panels.expedition import ExpeditionPanelMixin
from autowsgr.application.ui.pages.map.panels.sortie import (
    LootShipCount,
    SortiePanelMixin,
    recognize_loot_count,
    recognize_ship_count,
)


__all__ = [
    'CampaignPanelMixin',
    'DecisivePanelMixin',
    'ExercisePanelMixin',
    'ExpeditionPanelMixin',
    'LootShipCount',
    'SortiePanelMixin',
    'recognize_loot_count',
    'recognize_ship_count',
]
