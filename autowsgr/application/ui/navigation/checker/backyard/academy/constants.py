"""模块功能：维护学院二级页检查器的识别模板路径与识别区域。

上层调用：
- application.ui.navigation.checker.backyard.academy：读取本模块识别数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存识别模板路径与识别区域，不保存识别阈值、判定规则或点击坐标。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 模板根下的命名空间：二级页模板放在以页面命名的子目录里。
TEMPLATE_NAMESPACE = 'backyard/academy'

# 模板文件名；目录与命名空间已表达域，文件名不再重复域前缀。
PAGE_TEMPLATE = 'ACADEMY_PAGE_720P.png'

# 学院二级页页面身份的归一化区域，校准基准为 1280x720 截图。
PAGE_ROI = ROI(0.8508, 0.0181, 0.9969, 0.1028)
