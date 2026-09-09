"""模块功能：组合战斗地图页面的面板、章节、节点和远征操作能力。

上层调用：
- application.ui.navigation：执行母港、地图和决战之间的页面导航。
- business.combat、business.logistics：驱动地图面板业务流程。
- testing.ui：执行地图页面集成验证。

下层依赖：
- application.ui.controller.operations.sortie_page.battle_page.base：提供页面状态和通用面板动作。
- application.ui.controller.operations.sortie_page：提供各顶部标签业务面板 Mixin。

本模块只组合页面能力；地图 OCR 解析和跨页面业务策略由下层/上层对应模块负责。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.operations.sortie_page import (
    CampaignPanelMixin,
    DecisivePanelMixin,
    ExercisePanelMixin,
    ExpeditionPanelMixin,
    SortiePanelMixin,
)


class MapPage(
    SortiePanelMixin,
    CampaignPanelMixin,
    DecisivePanelMixin,
    ExercisePanelMixin,
    ExpeditionPanelMixin,
):
    """地图页面控制器。

    继承自所有面板 Mixin，提供完整的地图页面操作能力:

    - **出征** (:class:`SortiePanelMixin`): 章节导航、进入出征准备。
    - **战役** (:class:`CampaignPanelMixin`): 难度选择、进入战役。
    - **决战** (:class:`DecisivePanelMixin`): 进入决战总览。
    - **演习** (:class:`ExercisePanelMixin`): 对手检测、选择、战斗、刷新、阵容识别。
    - **远征** (:class:`ExpeditionPanelMixin`): 远征收取。

    公共查询方法 (页面识别、面板检测等) 和章节导航由
    :class:`~autowsgr.application.ui.controller.operations.sortie_page.battle_page.base.BaseMapPage` 提供。

    Parameters
    ----------
    ctrl:
        Android 设备控制器实例。
    ocr:
        OCR 引擎实例 (可选，章节导航时需要)。
    """
