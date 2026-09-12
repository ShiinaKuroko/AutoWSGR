"""模块功能：维护战役支援状态识别和切换所需的校准参数。

上层调用：
- campaign_support.recognition：读取战役支援状态。
- campaign_support.workflow：执行战役支援切换。

下层依赖：
- 无。
"""

from __future__ import annotations

from autowsgr.common.vision import Color


# ── 战役支援状态校准 ─────────────────────────────────────────────────────────

SUPPORT_ENABLE = Color.of(228, 182, 60)  # 战役支援可用颜色，用于判断支援已启用。
SUPPORT_DISABLE = Color.of(44, 142, 239)  # 战役支援关闭颜色，用于判断支援未启用。
SUPPORT_EXHAUSTED = Color.of(143, 145, 154)  # 支援耗尽颜色，用于阻止继续点击。
SUPPORT_PROBE = (0.6524, 0.1848)  # 战役支援状态探测点，用于读取开关颜色。
CLICK_SUPPORT = (0.6399, 0.1806)  # 战役支援按钮点击点，用于切换支援状态。


# ── 战役支援流程参数 ─────────────────────────────────────────────────────────

SUPPORT_SWITCH_WAIT = 0.5  # 支援开关点击后等待状态刷新的时间。


__all__ = [
    'CLICK_SUPPORT',
    'SUPPORT_DISABLE',
    'SUPPORT_ENABLE',
    'SUPPORT_EXHAUSTED',
    'SUPPORT_PROBE',
    'SUPPORT_SWITCH_WAIT',
]
