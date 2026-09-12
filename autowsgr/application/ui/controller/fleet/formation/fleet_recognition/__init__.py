"""模块功能：导出当前编队事实识别和快照补全入口。

上层调用：
- formation.workflow：编排编队识别和调整之间的事实交接。

下层依赖：
- fleet_recognition.recognition：执行舰名、槽位、舰种和等级识别。
- fleet_recognition.models：保存一次识别得到的编队事实。
"""

from autowsgr.application.ui.controller.fleet.formation.fleet_recognition.models import (
    FleetSnapshot,
)
from autowsgr.application.ui.controller.fleet.formation.fleet_recognition.recognition import (
    fill_missing_fleet_snapshot,
    read_fleet_snapshot,
)


__all__ = ['FleetSnapshot', 'fill_missing_fleet_snapshot', 'read_fleet_snapshot']
