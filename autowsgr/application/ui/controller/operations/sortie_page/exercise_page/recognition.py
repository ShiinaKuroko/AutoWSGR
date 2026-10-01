"""模块功能：从演习截图读取列表位置和对手挑战状态。

上层调用：
- application.ui.controller.operations.sortie_page.exercise_page.page：读取演习页面事实。

下层依赖：
- application.ui.controller.operations.sortie_page.exercise_page.constants：提供可见位置校准。
- common.vision：提供像素颜色匹配。

边界：
本模块只接收截图并返回视觉事实，不操作设备、不编排流程或决定页面导航。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.exercise_page import constants
from autowsgr.common.vision import PixelChecker
from autowsgr.common.vision.adapters.pixel_matching import Color


if TYPE_CHECKING:
    import numpy


# ── 列表位置识别参数 ────────────────────────────────────────────────────────

_ARROW_GRAY = Color.from_rgb_tuple((177, 171, 176))
_ARROW_COLOR_TOLERANCE = 60.0
_ARROW_UP_PROBE: tuple[float, float] = (0.9719, 0.1098)
_ARROW_DOWN_PROBE: tuple[float, float] = (0.9719, 0.9056)


# ── 挑战状态识别参数 ────────────────────────────────────────────────────────

_CHALLENGE_COLOR = Color.from_rgb_tuple((33, 132, 226))
_CHALLENGE_COLOR_TOLERANCE = 50.0


def check_rival_list_at_top(screen: numpy.ndarray) -> bool:
    """检查演习对手列表是否位于顶部。

    Args:
        screen: 演习页面 RGB 截图。

    Returns:
        顶部箭头颜色命中时返回 True。
    """
    return PixelChecker.check_pixel(
        screen,
        *_ARROW_UP_PROBE,
        _ARROW_GRAY,
        _ARROW_COLOR_TOLERANCE,
    )


def check_rival_list_at_bottom(screen: numpy.ndarray) -> bool:
    """检查演习对手列表是否位于底部。

    Args:
        screen: 演习页面 RGB 截图。

    Returns:
        底部箭头颜色命中时返回 True。
    """
    return PixelChecker.check_pixel(
        screen,
        *_ARROW_DOWN_PROBE,
        _ARROW_GRAY,
        _ARROW_COLOR_TOLERANCE,
    )


def check_rival_challenge_available(screen: numpy.ndarray, visible_slot: int) -> bool:
    """检查可见对手槽位是否显示可挑战按钮。

    Args:
        screen: 演习页面 RGB 截图。
        visible_slot: 可见对手槽位，范围为 0-3。

    Returns:
        挑战按钮颜色命中时返回 True。
    """
    coordinate = constants.RIVAL_CHALLENGE_POSITIONS[visible_slot]
    return PixelChecker.check_pixel(
        screen,
        *coordinate,
        _CHALLENGE_COLOR,
        _CHALLENGE_COLOR_TOLERANCE,
    )
