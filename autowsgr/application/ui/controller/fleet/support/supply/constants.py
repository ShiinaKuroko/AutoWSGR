"""模块功能：维护自动补给和快速补给流程的校准与同步参数。

上层调用：
- supply.recognition：读取自动补给状态。
- supply.workflow：切换自动补给和执行快速补给。

下层依赖：
- 无。
"""

from __future__ import annotations

from autowsgr.common.vision.operations.pixel_matching import Color


# ── 自动补给校准 ─────────────────────────────────────────────────────────────

AUTO_SUPPLY_ON = Color.of(13, 140, 233)  # 自动补给启用态颜色，用于确认补给策略已打开。
AUTO_SUPPLY_PROBE = (0.0555, 0.9348)  # 自动补给状态探测点，用于读取复选框颜色。
CLICK_AUTO_SUPPLY = (0.0954, 0.9348)  # 自动补给复选框点击点，用于切换补给策略。
STATE_TOLERANCE = 30.0  # 自动补给状态颜色容差，用于适配截图压缩和渲染差异。


# ── 快速补给流程参数 ─────────────────────────────────────────────────────────

SUPPLY_PANEL_WAIT = 0.5  # 打开快速补给面板后等待内容稳定的时间。
SUPPLY_SLOT_WAIT = 0.3  # 每个槽位补给点击后等待页面同步的时间。


__all__ = [
    'AUTO_SUPPLY_ON',
    'AUTO_SUPPLY_PROBE',
    'CLICK_AUTO_SUPPLY',
    'STATE_TOLERANCE',
    'SUPPLY_PANEL_WAIT',
    'SUPPLY_SLOT_WAIT',
]
