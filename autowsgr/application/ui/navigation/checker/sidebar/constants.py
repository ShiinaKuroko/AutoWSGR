"""模块功能：维护侧边栏检查器的识别模板路径与识别区域。

上层调用：
- application.ui.navigation.checker.sidebar：读取本模块识别数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存识别模板路径与识别区域，不保存识别阈值、判定规则或点击坐标。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 本模块在模板根下的命名空间，完整路径由公共校准模块拼接。
TEMPLATE_NAMESPACE = 'sidebar'

# 本模块的模板文件名；目录小写、文件名全大写。
SIDEBAR_MAIN_TEMPLATE = 'SIDEBAR_MAIN_720P.png'
BUILD_SUBMENU_TEMPLATE = 'SIDEBAR_BUILD_720P.png'
INTENSIFY_SUBMENU_TEMPLATE = 'SIDEBAR_INTENSIFY_720P.png'


# ── 侧边栏识别区域 ──────────────────────────────────────────────────────────

# 侧边栏展开时「商城」条目的归一化区域，校准基准为 1280x720 截图。
SIDEBAR_MAIN_ROI = ROI(0.0305, 0.0612, 0.2571, 0.1723)


# ── 二级菜单识别区域 ────────────────────────────────────────────────────────

# 点「建造」「改造」后右侧弹出的二级菜单首项区域，同一校准基准。
BUILD_SUBMENU_ROI = ROI(0.3024, 0.332, 0.475, 0.407)
INTENSIFY_SUBMENU_ROI = ROI(0.3024, 0.4612, 0.4719, 0.5375)
