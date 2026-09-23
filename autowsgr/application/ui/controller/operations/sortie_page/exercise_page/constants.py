"""模块功能：提供演习列表和对手信息页的静态校准数据。

上层调用：
- application.ui.controller.operations.sortie_page.exercise_page.operations：执行页面点击和滑动。
- application.ui.controller.operations.sortie_page.exercise_page.recognition：读取可见对手状态。

下层依赖：
- 无。

边界：
本模块只保存演习页面坐标和滑动校准数据，不保存识别阈值、设备对象或流程参数。
"""

from __future__ import annotations


# ── 演习列表 ─────────────────────────────────────────────────────────────────

# 可见对手挑战按钮位置，按屏幕从上到下排列。
RIVAL_CHALLENGE_POSITIONS: tuple[tuple[float, float], ...] = (
    (0.8024, 0.1848),
    (0.8024, 0.3889),
    (0.8024, 0.5931),
    (0.8024, 0.7959),
)

# 列表上滑坐标，用于显示对手 1-4。
SWIPE_TO_TOP: tuple[float, float, float, float] = (
    0.8336,
    0.3709,
    0.8336,
    0.7403,
)

# 列表下滑坐标，用于显示对手 5。
SWIPE_TO_BOTTOM: tuple[float, float, float, float] = (
    0.8336,
    0.7403,
    0.8336,
    0.3709,
)


# ── 对手信息页 ──────────────────────────────────────────────────────────────

# 对手信息页刷新按钮位置。
CLICK_RIVAL_REFRESH: tuple[float, float] = (0.6930, 0.7403)

# 演习开始按钮位置，用于进入出征准备页。
CLICK_START_BATTLE: tuple[float, float] = (0.8375, 0.7223)
