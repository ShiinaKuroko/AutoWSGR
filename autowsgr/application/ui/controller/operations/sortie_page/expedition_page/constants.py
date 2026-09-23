"""模块功能：维护远征页面槽位状态和结算操作的静态校准。

上层调用：
- application.ui.controller.operations.sortie_page.expedition_page.recognition：读取槽位状态校准。
- application.ui.controller.operations.sortie_page.expedition_page.operations：读取结算操作坐标。
- application.ui.controller.operations.sortie_page.expedition_page.page：读取槽位探测坐标。

下层依赖：
- 无。

本模块只保存远征页面的静态校准数据，不保存页面状态、设备对象或业务规则。
"""

from __future__ import annotations


# ── 槽位状态校准 ────────────────────────────────────────────────────────────

READY_COLOR: tuple[int, int, int] = (253, 228, 66)  # 远征完成颜色，用于识别可收取槽位。
SLOT_TOLERANCE: float = 30.0  # 远征槽位颜色容差，用于兼容截图渲染差异。
SLOT_PROBES: tuple[tuple[float, float], ...] = (
    (0.8516, 0.2736),  # 第 1 个远征槽位状态探测点。
    (0.8531, 0.4736),  # 第 2 个远征槽位状态探测点。
    (0.8539, 0.6667),  # 第 3 个远征槽位状态探测点。
    (0.8547, 0.8694),  # 第 4 个远征槽位状态探测点。
)

# ── 结算操作坐标 ────────────────────────────────────────────────────────────

CLICK_SKIP: tuple[float, float] = (0.7600, 0.5000)  # 远征结算跳过区域，用于结束奖励动画。

__all__ = [  # noqa: RUF022 - exports follow the calibration definition order
    'READY_COLOR',
    'SLOT_TOLERANCE',
    'SLOT_PROBES',
    'CLICK_SKIP',
]
