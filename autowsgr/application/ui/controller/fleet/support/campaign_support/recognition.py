"""模块功能：识别出征准备页的战役支援状态。

上层调用：
- campaign_support.workflow：判断是否需要切换战役支援。

下层依赖：
- campaign_support.constants：提供支援探测点和颜色。
- common.vision：读取像素颜色。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.fleet.support.campaign_support import constants
from autowsgr.common.vision import PixelChecker


if TYPE_CHECKING:
    import numpy


class SupportStatus(enum.Enum):
    """战役支援按钮的三种视觉状态。"""

    ENABLED = 'enabled'
    DISABLED = 'disabled'
    EXHAUSTED = 'exhausted'


def read_support_status(screen: numpy.ndarray) -> SupportStatus:
    """读取战役支援当前为启用、关闭还是次数耗尽。"""
    pixel = PixelChecker.get_pixel(screen, *constants.SUPPORT_PROBE)
    enable_distance = pixel.distance(constants.SUPPORT_ENABLE)
    disable_distance = pixel.distance(constants.SUPPORT_DISABLE)
    exhausted_distance = pixel.distance(constants.SUPPORT_EXHAUSTED)
    if enable_distance > exhausted_distance and disable_distance > exhausted_distance:
        return SupportStatus.EXHAUSTED
    if enable_distance < disable_distance:
        return SupportStatus.ENABLED
    return SupportStatus.DISABLED


def check_support_enabled(screen: numpy.ndarray) -> bool:
    """判断战役支援是否已启用或已耗尽且不应继续点击。"""
    return read_support_status(screen) is not SupportStatus.DISABLED


__all__ = ['SupportStatus', 'check_support_enabled', 'read_support_status']
