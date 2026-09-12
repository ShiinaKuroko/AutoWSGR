"""模块功能：识别出征准备页的自动补给开关状态。

上层调用：
- supply.workflow：决定是否需要执行快速补给。

下层依赖：
- supply.constants：提供自动补给探测点和颜色。
- common.vision：读取像素颜色。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.fleet.support.supply import constants
from autowsgr.common.vision import PixelChecker


if TYPE_CHECKING:
    import numpy


def check_auto_supply_enabled(screen: numpy.ndarray) -> bool:
    """判断准备页自动补给是否已启用。"""
    return PixelChecker.get_pixel(
        screen,
        *constants.AUTO_SUPPLY_PROBE,
    ).near(
        constants.AUTO_SUPPLY_ON,
        constants.STATE_TOLERANCE,
    )


__all__ = ['check_auto_supply_enabled']
