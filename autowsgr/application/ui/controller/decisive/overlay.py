"""决战地图页 Overlay 枚举、像素签名与坐标常量。

决战地图页上可能叠加以下三种弹窗::

    FLEET_ACQUISITION  战备舰队获取 — 选择购买舰船/技能
    CONFIRM_EXIT       确认退出     — 暂离(保存) 或 撤退(清空)
    ADVANCE_CHOICE     选择前进点   — 多路径分支选择

每种弹窗均由 ``PixelSignature`` 识别。
``detect_decisive_overlay()`` 按优先级顺序依次检测并返回首个命中结果。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.common.calibration.decisive import (
    ADVANCE_CARD_POSITIONS,
    CLICK_ADVANCE_CONFIRM,
    CLICK_FLEET_CLOSE,
    CLICK_FLEET_REFRESH,
    CLICK_FORMATION,
    CLICK_LEAVE,
    CLICK_RETREAT_BUTTON,
    CLICK_RETREAT_CONFIRM,
    CLICK_SORTIE,
    COST_AREA,
    FLEET_CARD_CLICK_Y,
    FLEET_CARD_X_POSITIONS,
    RESOURCE_AREA,
    SHIP_NAME_X_RANGES,
    SHIP_NAME_Y_RANGE,
    SIG_ADVANCE_CHOICE,
    SIG_CONFIRM_EXIT,
    SIG_FLEET_ACQUISITION,
    SIG_MAP_PAGE,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import (
    ImageChecker,
    ImageTemplate,
    PixelChecker,
    PixelSignature,
)
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np


_log = get_logger('ui.decisive')

# ═══════════════════════════════════════════════════════════════════════════════
# 枚举
# ═══════════════════════════════════════════════════════════════════════════════


class DecisiveOverlay(enum.Enum):
    """决战地图页上的弹窗类型。"""

    FLEET_ACQUISITION = 'fleet_acquisition'
    """战备舰队获取 — 选择购买舰船/技能。"""

    CONFIRM_EXIT = 'confirm_exit'
    """确认退出 — 暂离或撤退。"""

    ADVANCE_CHOICE = 'advance_choice'
    """选择前进点 — 分支路径选择。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 像素签名
# ═══════════════════════════════════════════════════════════════════════════════

# ── 战备舰队获取 ──
# 特征: 顶部「战备舰队获取」白色标题 + 底部刷新/关闭按钮区域

# ── 确认退出 ──
# 特征: 左「暂离」蓝色按钮 + 右「撤退」红色按钮 + 对话框灰色背景

# ── 选择前进点 ──
# 特征: 底部「确认」蓝色按钮 + 右侧编队/出征按钮变为深色背景 (被遮挡)

# ── 决战地图页 (无 overlay) ──
# 特征: 左上角撤退按钮橙色 + 右下角编队/出征三个蓝色按钮

# 按优先级排列的 overlay → 签名映射
OVERLAY_SIGNATURES: list[tuple[DecisiveOverlay, PixelSignature]] = [
    (DecisiveOverlay.FLEET_ACQUISITION, SIG_FLEET_ACQUISITION),
    (DecisiveOverlay.CONFIRM_EXIT, SIG_CONFIRM_EXIT),
    (DecisiveOverlay.ADVANCE_CHOICE, SIG_ADVANCE_CHOICE),
]

_SIG_BY_TYPE: dict[DecisiveOverlay, PixelSignature] = dict(OVERLAY_SIGNATURES)

# overlay → 识别模板映射 (图像模板匹配, 替代上方像素签名)
_OVERLAY_TEMPLATE_MAP: dict[DecisiveOverlay, ImageTemplate] = {
    DecisiveOverlay.FLEET_ACQUISITION: Templates.Decisive.FLEET_ACQUISITION,
    DecisiveOverlay.CONFIRM_EXIT: Templates.Decisive.CONFIRM_EXIT,
    DecisiveOverlay.ADVANCE_CHOICE: Templates.Decisive.ADVANCE_CHOICE,
}


# ═══════════════════════════════════════════════════════════════════════════════
# 坐标常量 (相对坐标 0.0-1.0, 参考分辨率 960x540)
# ═══════════════════════════════════════════════════════════════════════════════

# ── 决战地图页通用 ──




# ── 战备舰队获取 overlay ──









# ── 确认退出 overlay ──



# ── 选择前进点 overlay ──




# ═══════════════════════════════════════════════════════════════════════════════
# 检测函数
# ═══════════════════════════════════════════════════════════════════════════════


def detect_decisive_overlay(screen: np.ndarray) -> DecisiveOverlay | None:
    """按优先级检测决战地图页上的弹窗。

    Parameters
    ----------
    screen:
        截图 (HxWx3, RGB)。

    Returns
    -------
    DecisiveOverlay | None
        首个命中的弹窗类型；无弹窗则返回 ``None``。
    """
    for overlay_type, tmpl in _OVERLAY_TEMPLATE_MAP.items():
        if ImageChecker.template_exists(screen, tmpl, confidence=0.85):
            _log.debug('[决战] 检测到 overlay: {}', overlay_type.value)
            return overlay_type
    return None


def is_decisive_map_page(screen: np.ndarray) -> bool:
    """截图是否为决战地图页 (无 overlay 遮挡)。"""
    return PixelChecker.check_signature(screen, SIG_MAP_PAGE).matched


def is_fleet_acquisition(screen: np.ndarray) -> bool:
    """截图是否为战备舰队获取 overlay。"""
    return ImageChecker.template_exists(
        screen, Templates.Decisive.FLEET_ACQUISITION, confidence=0.85
    )


def get_overlay_template(overlay: DecisiveOverlay) -> ImageTemplate:
    """按类型获取对应的识别模板。"""
    return _OVERLAY_TEMPLATE_MAP[overlay]


def get_overlay_signature(overlay: DecisiveOverlay) -> PixelSignature:
    """按类型获取对应的像素签名 (保留备查, 不再参与判定)。"""
    return _SIG_BY_TYPE[overlay]
