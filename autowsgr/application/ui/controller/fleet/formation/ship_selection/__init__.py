"""模块功能：提供编队选船节点的页面和单舰选择入口。

上层调用：
- formation.fleet_adjustment：传入目标舰船规则并执行单槽位选择或移除。

下层依赖：
- ship_selection.page：提供船池页面 UI 原子动作。
- ship_selection.workflow：编排搜索、识别、点击和返回。

本包不导出船卡 OCR、约束判断或页面校准。
"""

from autowsgr.application.ui.controller.fleet.formation.ship_selection.page import (
    ShipSelectionPage,
)
from autowsgr.application.ui.controller.fleet.formation.ship_selection.workflow import (
    remove_ship,
    select_ship,
)


__all__ = ['ShipSelectionPage', 'remove_ship', 'select_ship']
