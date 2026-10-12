"""模块功能：维护主页的点击落点与通知探针。

上层调用：
- application.ui.controller.home.main_page.page：读取主页点击落点。
- application.ui.controller.home.main_page.recognition：读取通知探针。

下层依赖：
- common.vision：提供颜色与像素规则类型。

边界：只保存静态校准数据，不识别画面、不编排流程、不持有运行状态。
"""

from __future__ import annotations

from autowsgr.common.vision.adapters.pixel_matching import Color, PixelRule, PixelSignature


# ── 主页导航落点 ────────────────────────────────────────────────────────────

# 坐标为 1280x720 参考画面的归一化值；键与 Target 枚举名一致。
NAV_POSITIONS = {
    'sortie': (0.9430, 0.9069),
    'task': (0.6844, 0.9326),
    'sidebar': (0.0480, 0.8931),
    'backyard': (0.0508, 0.1535),
    'event': (0.8844, 0.4833),
}


# ── 每日浮窗按钮落点 ────────────────────────────────────────────────────────

# 坐标为 1280x720 归一化值，由静态样本做模板匹配实测（score=1.000）。
OVERLAY_POSITIONS = {
    'news_checkbox': (0.0625, 0.9049),
    'news_close': (0.0352, 0.0625),
    'reward_claim': (0.5000, 0.6653),
    'reward_confirm': (0.5020, 0.5694),
}


# ── 通知探针 ────────────────────────────────────────────────────────────────

# 通知红点的颜色与容差：只在本模块内构造探针，远征与任务共用。
_NOTIFICATION_RED = Color(255, 89, 45)
_NOTIFICATION_RED_TOLERANCE = 40.0

# 主页两个通知探针的像素规则：探针位置命中通知红即视为通知出现。
EXPEDITION_READY_SIGNATURE = PixelSignature(
    name='expedition_ready',
    rules=(
        PixelRule(
            x=0.9719,
            y=0.8403,
            color=_NOTIFICATION_RED,
            tolerance=_NOTIFICATION_RED_TOLERANCE,
        ),
    ),
)
TASK_READY_SIGNATURE = PixelSignature(
    name='task_ready',
    rules=(
        PixelRule(
            x=0.7227,
            y=0.8458,
            color=_NOTIFICATION_RED,
            tolerance=_NOTIFICATION_RED_TOLERANCE,
        ),
    ),
)


__all__ = [
    'EXPEDITION_READY_SIGNATURE',
    'NAV_POSITIONS',
    'OVERLAY_POSITIONS',
    'TASK_READY_SIGNATURE',
]
