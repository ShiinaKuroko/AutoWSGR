"""任务页面子包 — 页面识别 / 状态查询 / 操作动作。

UI 基础实现的归属地 (与 main_page / map 同级)。
"""

from autowsgr.application.ui.controller.operations.mission_page.page import (
    MissionPage,
    MissionPanel,
)
from autowsgr.application.ui.controller.operations.mission_page.recognition import (
    ButtonType,
    MissionInfo,
)


__all__ = [
    'ButtonType',
    'MissionInfo',
    'MissionPage',
    'MissionPanel',
]
