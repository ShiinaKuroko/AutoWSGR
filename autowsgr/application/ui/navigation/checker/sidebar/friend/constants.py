"""模块功能：维护好友页面检查器的识别模板路径与识别区域。

上层调用：
- application.ui.navigation.checker.sidebar.friend：读取本模块识别数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存识别模板路径与识别区域，不保存识别阈值、判定规则或点击坐标。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 本模块在模板根下的命名空间：好友从侧边栏进入，因此嵌在 sidebar 命名空间下。
TEMPLATE_NAMESPACE = 'sidebar/friend'

# 本模块的模板文件名；目录小写、文件名全大写。
# 好友页面有两个页签，账号设置不同进入后停留的页签也不同，两个都要认。
FRIEND_TAB_TEMPLATE = 'FRIEND_TAB_720P.png'
FRIEND_ADD_TAB_TEMPLATE = 'FRIEND_ADD_TAB_720P.png'


# ── 好友页面识别区域 ────────────────────────────────────────────────────────

# 两个页签各自的归一化区域，校准基准为 1280x720 截图。
# 尺寸都比对应模板大 1px 以上，避免换算截断后区域小于模板。
# 「好友」页签（模板 86x46，区域 88x48）。
FRIEND_TAB_ROI = ROI(0.1484, 0.0139, 0.2172, 0.0806)
# 「添加」页签（模板 94x42，区域 96x44）。
FRIEND_ADD_TAB_ROI = ROI(0.4016, 0.0194, 0.4766, 0.0806)
