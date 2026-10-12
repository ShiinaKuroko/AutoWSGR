"""模块功能：维护改造页面检查器的识别模板路径与识别区域。

上层调用：
- application.ui.navigation.checker.sidebar.intensify：读取本模块识别数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存识别模板路径与识别区域，不保存识别阈值、判定规则或点击坐标。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 本模块在模板根下的命名空间：改造页从侧边栏进入，因此嵌在 sidebar 命名空间下。
TEMPLATE_NAMESPACE = 'sidebar/intensify'

# 本模块的模板文件名；目录小写、文件名全大写。
# 改造页默认落在「强化」标签，因此用它作为页面身份。
INTENSIFY_TAB_TEMPLATE = 'SIDEBAR_INTENSIFY_TAB_720P.png'
REMOLD_TAB_TEMPLATE = 'SIDEBAR_INTENSIFY_REMOLD_TAB_720P.png'
SKILL_TAB_TEMPLATE = 'SIDEBAR_INTENSIFY_SKILL_TAB_720P.png'


# ── 改造页面识别区域 ────────────────────────────────────────────────────────

# 改造页三个标签的归一化区域，校准基准为 1280x720 截图。
INTENSIFY_TAB_ROI = ROI(0.15, 0.0167, 0.218, 0.0792)
REMOLD_TAB_ROI = ROI(0.2782, 0.0195, 0.3461, 0.0778)
SKILL_TAB_ROI = ROI(0.4086, 0.0139, 0.4735, 0.0778)
