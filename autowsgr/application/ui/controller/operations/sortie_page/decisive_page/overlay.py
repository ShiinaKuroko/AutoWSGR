"""模块功能：识别决战地图上的浮层类型和地图页面视觉状态。

上层调用：
- application.ui.controller.operations.sortie_page.decisive_page.map_page：读取浮层和地图状态。
- testing.ui、testing.ops：验证决战浮层和恢复链路。

下层依赖：
- application.ui.controller.operations.sortie_page.decisive_page.constants：提供像素签名。
- common.vision：执行模板和像素签名匹配。

本模块只负责视觉状态识别，不点击设备、不执行 OCR，也不决定决战业务阶段。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.decisive_page.constants import (
    SIG_ADVANCE_CHOICE,
    SIG_CONFIRM_EXIT,
    SIG_FLEET_ACQUISITION,
    SIG_MAP_PAGE,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import ImageChecker, ImageTemplate, PixelChecker, PixelSignature
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np


_log = get_logger('ui.decisive')


class DecisiveOverlay(enum.Enum):
    """决战地图上的浮层类型。"""

    FLEET_ACQUISITION = 'fleet_acquisition'
    """战备舰队获取浮层，用于选择购买舰船或技能。"""

    CONFIRM_EXIT = 'confirm_exit'
    """退出确认浮层，用于选择暂离或撤退。"""

    ADVANCE_CHOICE = 'advance_choice'
    """前进路线选择浮层，用于选择决战分支路线。"""


_OVERLAY_SIGNATURES: tuple[tuple[DecisiveOverlay, PixelSignature], ...] = (
    (DecisiveOverlay.FLEET_ACQUISITION, SIG_FLEET_ACQUISITION),
    (DecisiveOverlay.CONFIRM_EXIT, SIG_CONFIRM_EXIT),
    (DecisiveOverlay.ADVANCE_CHOICE, SIG_ADVANCE_CHOICE),
)
_SIG_BY_TYPE = dict(_OVERLAY_SIGNATURES)
_OVERLAY_TEMPLATE_MAP: dict[DecisiveOverlay, ImageTemplate] = {
    DecisiveOverlay.FLEET_ACQUISITION: Templates.Decisive.FLEET_ACQUISITION,
    DecisiveOverlay.CONFIRM_EXIT: Templates.Decisive.CONFIRM_EXIT,
    DecisiveOverlay.ADVANCE_CHOICE: Templates.Decisive.ADVANCE_CHOICE,
}


def check_decisive_map_page(screen: np.ndarray) -> bool:
    """检查截图是否为没有浮层遮挡的决战地图页。"""
    return PixelChecker.check_signature(screen, SIG_MAP_PAGE).matched


def check_fleet_acquisition(screen: np.ndarray) -> bool:
    """检查截图是否为战备舰队获取浮层。"""
    return ImageChecker.template_exists(
        screen,
        Templates.Decisive.FLEET_ACQUISITION,
        confidence=0.85,
    )


def read_overlay_type(screen: np.ndarray) -> DecisiveOverlay | None:
    """按优先级读取截图中的决战浮层类型。

    Args:
        screen: RGB 截图。

    Returns:
        首个匹配的浮层类型；没有浮层时返回 ``None``。
    """
    for overlay_type, template in _OVERLAY_TEMPLATE_MAP.items():
        if ImageChecker.template_exists(screen, template, confidence=0.85):
            _log.debug('[决战] 检测到浮层: {}', overlay_type.value)
            return overlay_type
    return None


def read_overlay_template(overlay: DecisiveOverlay) -> ImageTemplate:
    """读取指定浮层对应的模板。"""
    return _OVERLAY_TEMPLATE_MAP[overlay]


def read_overlay_signature(overlay: DecisiveOverlay) -> PixelSignature:
    """读取指定浮层对应的像素签名。"""
    return _SIG_BY_TYPE[overlay]


__all__ = [
    'DecisiveOverlay',
    'check_decisive_map_page',
    'check_fleet_acquisition',
    'read_overlay_signature',
    'read_overlay_template',
    'read_overlay_type',
]
