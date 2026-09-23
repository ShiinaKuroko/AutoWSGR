"""模块功能：维护任务页面的点击和滑动坐标。

上层调用：
- application.ui.controller.operations.mission_page.page：读取返回和任务面板坐标。
- application.ui.controller.operations.mission_page.operations：读取任务列表滑动坐标。

下层依赖：
- 无。

边界：
只保存任务页面共享的物理坐标，不保存操作时序、识别算法参数、页面状态或设备对象。
"""

from __future__ import annotations


# ── 页面动作坐标 ────────────────────────────────────────────────────────────────────

CLICK_BACK: tuple[float, float] = (0.0219, 0.0584)  # 返回母港主页的按钮坐标。
PANEL_POSITIONS: dict[str, tuple[float, float]] = {
    'all': (0.1540, 0.0667),  # 全部任务面板入口。
    'main': (0.2797, 0.0680),  # 主线任务面板入口。
    'daily': (0.4047, 0.0612),  # 日常任务面板入口。
    'weekly': (0.5407, 0.0584),  # 周常任务面板入口。
    'timed': (0.6672, 0.0570),  # 限时任务面板入口。
}
SCROLL: tuple[float, float, float, float] = (
    0.5000,
    0.7000,
    0.5000,
    0.4500,
)  # 任务列表滑动坐标，用于显示后续任务。


__all__ = [
    'CLICK_BACK',
    'PANEL_POSITIONS',
    'SCROLL',
]
