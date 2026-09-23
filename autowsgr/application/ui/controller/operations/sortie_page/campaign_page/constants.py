"""模块功能：维护战役页面的入口和难度切换坐标。

上层调用：
- application.ui.controller.operations.sortie_page.campaign_page.page：读取页面动作坐标。

下层依赖：
- 无。

边界：
只保存战役页面共享的点击坐标，不保存识别参数、流程时序、页面状态或设备对象。
"""

from __future__ import annotations


# ── 战役页面动作坐标 ───────────────────────────────────────────────────────────────

CAMPAIGN_POSITIONS: dict[int, tuple[float, float]] = {
    1: (0.1704, 0.5000),  # 航母战役入口。
    2: (0.3399, 0.5000),  # 潜艇战役入口。
    3: (0.5102, 0.5000),  # 驱逐战役入口。
    4: (0.6797, 0.5000),  # 巡洋战役入口。
    5: (0.8500, 0.5000),  # 战列战役入口。
}
CLICK_DIFFICULTY: tuple[float, float] = (0.8000, 0.1306)  # 难度切换按钮坐标。


__all__ = [
    'CAMPAIGN_POSITIONS',
    'CLICK_DIFFICULTY',
]
