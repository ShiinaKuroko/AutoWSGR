"""模块功能：维护主页的点击落点与通知探针。

上层调用：
- application.ui.controller.home.main_page.page：读取主页点击落点。
- application.ui.controller.home.main_page.recognition：读取通知探针与颜色。

下层依赖：
- common.vision：提供颜色类型。

边界：只保存静态校准数据，不识别画面、不编排流程、不持有运行状态。
"""

from __future__ import annotations

from autowsgr.common.vision.adapters.pixel_matching import Color


# ── 主页导航落点 ────────────────────────────────────────────────────────────────────

# 坐标为 1280x720 参考画面的归一化值；键与 Target 枚举名一致。
NAV_POSITIONS = {
    'sortie': (0.9430, 0.9069),
    'task': (0.6836, 0.9042),
    'sidebar': (0.0516, 0.8972),
    'backyard': (0.0484, 0.1556),
    'event': (0.8844, 0.4833),
}


# ── 每日浮窗点击落点 ──────────────────────────────────────────────────────────────────

# 公告关闭按钮的落点；其余浮窗按钮的落点由识别产出后由调用方传入。
DISMISS_POSITIONS = {
    'news_close': (0.0352, 0.0625),
}


# ── 通知探针 ──────────────────────────────────────────────────────────────────────

# 通知红点的采样位置与颜色判定参数。
PROBE_POSITIONS = {
    'expedition_ready': (0.9719, 0.8403),
    'task_ready': (0.7227, 0.8458),
}

NOTIFICATION_RED = Color(255, 89, 45)
NOTIFICATION_RED_TOLERANCE = 40.0


__all__ = [
    'DISMISS_POSITIONS',
    'NAV_POSITIONS',
    'NOTIFICATION_RED',
    'NOTIFICATION_RED_TOLERANCE',
    'PROBE_POSITIONS',
]
