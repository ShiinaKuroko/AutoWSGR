"""面板 Mixin 子包。"""

from autowsgr.infra.base.combat.map.panels.campaign import CampaignPanelMixin
from autowsgr.infra.base.combat.map.panels.decisive import DecisivePanelMixin
from autowsgr.infra.base.combat.map.panels.exercise import ExercisePanelMixin
from autowsgr.infra.base.combat.map.panels.expedition import ExpeditionPanelMixin
from autowsgr.infra.base.combat.map.panels.sortie import (
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
