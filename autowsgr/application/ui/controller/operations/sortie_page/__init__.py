"""模块功能：聚合地图顶部标签中的出征、演习、战役、远征和决战面板。

上层调用：
- application.ui.controller.operations.sortie_page.battle_page.page：组合五个面板 Mixin，形成完整地图页面控制器。
- business.combat、business.logistics：通过 `MapPage` 调用对应面板动作。

下层依赖：
- application.ui.controller.operations.sortie_page.battle_page.base：提供地图页面共享状态和公共面板动作。
- application.ui.controller.operations.sortie_page：提供五个面板 Mixin 实现。

本包只负责顶部标签模块的目录归属和稳定导出，不保存运行时状态或业务调度规则。
"""

from autowsgr.application.ui.controller.operations.sortie_page.campaign_page import (
    CampaignPanelMixin,
)
from autowsgr.application.ui.controller.operations.sortie_page.decisive import DecisivePanelMixin
from autowsgr.application.ui.controller.operations.sortie_page.exercise_page import (
    ExercisePanelMixin,
)
from autowsgr.application.ui.controller.operations.sortie_page.expedition_page import (
    ExpeditionPanelMixin,
)
from autowsgr.application.ui.controller.operations.sortie_page.sortie import SortiePanelMixin


__all__ = [
    'CampaignPanelMixin',
    'DecisivePanelMixin',
    'ExercisePanelMixin',
    'ExpeditionPanelMixin',
    'SortiePanelMixin',
]
