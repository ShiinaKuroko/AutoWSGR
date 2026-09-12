"""模块功能：导出任务页面的状态读取、任务识别和奖励操作控制器。

上层调用：
- application.ui.navigation：注册任务页面检查器和回退动作。
- business：读取任务并触发奖励领取。

下层依赖：
- application.ui.controller.operations.mission_page.page：提供任务页面 UI 行为。
- application.ui.controller.operations.mission_page.recognition：提供任务 OCR 结果和解析。

任务页面包与 home、backyard、sidebar 页面组同级管理。
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
