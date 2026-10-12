"""模块功能：维护建造页面检查器的识别模板路径与识别区域。

上层调用：
- application.ui.navigation.checker.sidebar.build：读取本模块识别数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存识别模板路径与识别区域，不保存识别阈值、判定规则或点击坐标。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 本模块在模板根下的命名空间：建造页从侧边栏进入，因此嵌在 sidebar 命名空间下。
TEMPLATE_NAMESPACE = 'sidebar/build'

# 本模块的模板文件名；目录小写、文件名全大写。
# 建造页默认落在「建造」标签，因此用它作为页面身份。
BUILD_TAB_TEMPLATE = 'SIDEBAR_BUILD_TAB_720P.png'
DISMANTLE_TAB_TEMPLATE = 'SIDEBAR_BUILD_DISMANTLE_TAB_720P.png'


# ── 建造页面识别区域 ────────────────────────────────────────────────────────

# 建造页四个标签中已采样的两个；校准基准为 1280x720 截图。
BUILD_TAB_ROI = ROI(0.1485, 0.0167, 0.2188, 0.0792)
DISMANTLE_TAB_ROI = ROI(0.2782, 0.0153, 0.3469, 0.0806)
