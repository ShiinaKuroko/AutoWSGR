"""定义主页坐标、感兴趣区域和通知颜色校准数据。"""

from __future__ import annotations

from autowsgr.common.vision.adapters.pixel_matching import Color
from autowsgr.common.vision.adapters.template_matching import ROI


# -- 主页导航坐标 -----------------------------------------------------------

NAV_POSITIONS = {
    'sortie': (0.9430, 0.9069),
    'task': (0.6836, 0.9042),
    'sidebar': (0.0516, 0.8972),
    'backyard': (0.0484, 0.1556),
    'event': (0.8844, 0.4833),
}


# -- 通知探针 ---------------------------------------------------------------

PROBE_POSITIONS = {
    'expedition_ready': (0.9719, 0.8403),
    'task_ready': (0.7227, 0.8458),
}

NOTIFICATION_RED = Color(255, 89, 45)
NOTIFICATION_RED_TOLERANCE = 40.0


# -- 主页浮窗区域 -----------------------------------------------------------

DISMISS_POSITIONS = {
    'news_close': (0.0352, 0.0625),
}

NEWS_TEXT_ROI = ROI(0.08671875, 0.87638889, 0.21250000, 0.94027778)
"""公告标题区域，边界比模板各方向扩大 1 像素。"""

NEWS_CHECKBOX_ROI = ROI(0.03828125, 0.86527778, 0.08750000, 0.94583333)
"""公告勾选框区域，边界比模板各方向扩大 1 像素。"""

REWARD_TEXT_ROI = ROI(0.10156250, 0.26805556, 0.33125000, 0.33611111)
"""每日奖励标题区域，边界比模板各方向扩大 1 像素。"""

REWARD_CLAIM_BUTTON_ROI = ROI(0.44062500, 0.62916667, 0.55937500, 0.70277778)
"""每日奖励领取按钮区域，边界比模板各方向扩大 1 像素。"""

REWARD_CONFIRM_BUTTON_ROI = ROI(0.43515625, 0.51944444, 0.56953125, 0.62083333)
"""奖励确认按钮区域，边界比模板各方向扩大 1 像素。"""


__all__ = [
    'DISMISS_POSITIONS',
    'NAV_POSITIONS',
    'NEWS_CHECKBOX_ROI',
    'NEWS_TEXT_ROI',
    'NOTIFICATION_RED',
    'NOTIFICATION_RED_TOLERANCE',
    'PROBE_POSITIONS',
    'REWARD_CLAIM_BUTTON_ROI',
    'REWARD_CONFIRM_BUTTON_ROI',
    'REWARD_TEXT_ROI',
]
