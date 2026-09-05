"""面板 Mixin 子包。"""

from autowsgr.application.ui.controller.map.panels.campaign import CampaignPanelMixin
from autowsgr.application.ui.controller.map.panels.decisive import DecisivePanelMixin
from autowsgr.application.ui.controller.map.panels.exercise import ExercisePanelMixin
from autowsgr.application.ui.controller.map.panels.expedition import ExpeditionPanelMixin
from autowsgr.application.ui.controller.map.panels.sortie import SortiePanelMixin


__all__ = [
    'CampaignPanelMixin',
    'DecisivePanelMixin',
    'ExercisePanelMixin',
    'ExpeditionPanelMixin',
    'SortiePanelMixin',
]
