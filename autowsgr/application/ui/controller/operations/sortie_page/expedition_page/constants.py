"""模块功能：维护远征面板的槽位颜色、探测点和容差常量。

上层调用：
- application.ui.controller.operations.sortie_page.expedition_page.page：读取远征槽位校准。

下层依赖：
- 无。

本模块只保存远征页面的静态校准数据，不保存页面状态、设备对象或业务规则。
"""

from __future__ import annotations


READY_COLOR = (253, 228, 66)  # 远征完成颜色，用于识别可收取槽位。
SLOT_TOLERANCE: float = 30.0  # 远征槽位颜色容差，用于兼容截图渲染差异。
SLOT_PROBES = (
    (0.8516, 0.2736),  # 第 1 个远征槽位状态探测点。
    (0.8531, 0.4736),  # 第 2 个远征槽位状态探测点。
    (0.8539, 0.6667),  # 第 3 个远征槽位状态探测点。
    (0.8547, 0.8694),  # 第 4 个远征槽位状态探测点。
)


__all__ = ['READY_COLOR', 'SLOT_PROBES', 'SLOT_TOLERANCE']
