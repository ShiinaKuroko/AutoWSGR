"""模块功能：读取远征页面可收取槽位的像素事实。

上层调用：
- application.ui.controller.operations.sortie_page.expedition_page.page：读取可收取槽位。

下层依赖：
- application.ui.controller.operations.sortie_page.expedition_page.constants：提供槽位探测点和颜色校准。
- common.system.logger：记录必要的识别事实。
- common.vision：读取像素颜色并执行容差比较。

本模块只接收截图并返回槽位事实，不执行设备操作、页面导航或远征流程编排。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.expedition_page import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision.operations.pixel_matching import Color
from autowsgr.common.vision import PixelChecker


if TYPE_CHECKING:
    import numpy as np


_log = get_logger('ui.sortie.expedition_page.recognition')
_READY_COLOR = Color.from_rgb_tuple(constants.READY_COLOR)


def read_ready_expedition_slot(screen: np.ndarray) -> int | None:
    """读取远征槽位并返回第一个已完成槽位。

    Args:
        screen: 远征页面 RGB 截图。

    Returns:
        已完成槽位索引（0-3）；没有可收取远征时返回 None。
    """
    for slot_index, (probe_x, probe_y) in enumerate(constants.SLOT_PROBES):
        actual = PixelChecker.get_pixel(screen, probe_x, probe_y)
        if actual.near(_READY_COLOR, constants.SLOT_TOLERANCE):
            _log.debug(
                '[UI] 远征页 → 识别：槽位索引={}，实际颜色={!r}，期望颜色={!r}',
                slot_index,
                actual.as_rgb_tuple(),
                constants.READY_COLOR,
            )
            return slot_index
    return None


__all__ = ['read_ready_expedition_slot']
