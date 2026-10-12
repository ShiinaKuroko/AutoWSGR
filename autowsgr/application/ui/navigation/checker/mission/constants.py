"""模块功能：维护任务页检查器的识别模板路径与识别区域。

上层调用：
- application.ui.navigation.checker.mission：读取本模块识别数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存识别模板路径与识别区域，不保存识别阈值、判定规则或点击坐标。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 本模块在模板根下的命名空间，完整路径由公共校准模块拼接。
TEMPLATE_NAMESPACE = 'mission'

# 本模块的模板文件名；目录小写、文件名全大写。
# 任务页默认落在「全部」页签，因此用它作为页面身份。
ALL_TAB_TEMPLATE = 'MISSION_ALL_TAB_720P.png'
CLAIM_ALL_BUTTON_TEMPLATE = 'MISSION_CLAIM_ALL_720P.png'
REWARD_CONFIRM_BUTTON_TEMPLATE = 'MISSION_REWARD_CONFIRM_720P.png'


# ── 任务页识别区域 ──────────────────────────────────────────────────────────

# 顶部「全部」页签的归一化区域，校准基准为 1280x720 截图。
ALL_TAB_ROI = ROI(0.1477, 0.0223, 0.2204, 0.0848)


# ── 领奖与确认区域 ──────────────────────────────────────────────────────────

# 右下角「全部领取」按钮与「获得」浮窗里的「确认」按钮，同一校准基准。
CLAIM_ALL_BUTTON_ROI = ROI(0.8157, 0.9181, 0.9243, 0.9848)
REWARD_CONFIRM_BUTTON_ROI = ROI(0.4399, 0.6098, 0.554, 0.6889)
