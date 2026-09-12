"""模块功能：导出编队调整节点的流程对象。

上层调用：
- formation.workflow：调用编队调整节点完成成员集合、槽位和顺序处理。

下层依赖：
- fleet_adjustment.workflow：编排规则、规划、对齐和模式分支。

本包不导出规则、规划和页面动作的内部实现。
"""

from autowsgr.application.ui.controller.fleet.formation.fleet_adjustment.workflow import (
    FleetAdjustment,
)


__all__ = ['FleetAdjustment']
