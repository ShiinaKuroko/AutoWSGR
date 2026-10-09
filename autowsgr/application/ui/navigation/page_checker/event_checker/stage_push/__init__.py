"""模块功能：提供普通推图活动 checker 的模块入口。

上层调用：
- application.ui.navigation.page_checker.event_checker：导出本活动 checker。
- application.ui.navigation：按活动玩法调用本 checker 的页面识别入口。

下层依赖：
- event_checker.stage_push.checker：提供页面识别入口与页面事实模型。
- event_checker.stage_push.recognition：提供活动难度事实。

本模块只导出稳定入口与事实模型，不放业务实现。
"""

from __future__ import annotations

from autowsgr.application.ui.navigation.page_checker.event_checker.stage_push.checker import (
    EventMapState,
    EventStage,
    check_event_entry,
    check_event_sortie_prepare,
    parse_stage,
    read_event_map_state,
)
from autowsgr.application.ui.navigation.page_checker.event_checker.stage_push.recognition import (
    EventMode,
)


__all__ = [
    'EventMapState',
    'EventMode',
    'EventStage',
    'check_event_entry',
    'check_event_sortie_prepare',
    'parse_stage',
    'read_event_map_state',
]
