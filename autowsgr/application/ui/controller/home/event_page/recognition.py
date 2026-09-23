"""模块功能：读取活动地图页面的视觉事实。

上层调用：
- application.ui.controller.home.event_page.page：获取活动地图页面事实。

下层依赖：
- application.ui.controller.home.event_page.constants：提供页面 ROI 和颜色校准。
- common.vision 与 common.vision.resources.pages.event：提供识别基础能力和模板。

边界：
本模块只接收截图并返回识别结果，不执行设备操作、页面导航或流程控制。
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home.event_page import constants
from autowsgr.common import vision
from autowsgr.application.vision.resources.pages import event


if TYPE_CHECKING:
    import numpy


_TEMPLATE_MATCH_CONFIDENCE = 0.8  # 活动地图模板匹配的最低置信度。


# ── 页面视觉事实 ─────────────────────────────────────────────────────────────


def read_fight_button_detail(
    screen: numpy.ndarray,
) -> vision.ImageMatchDetail | None:
    """读取节点详情浮层中的出击按钮匹配结果。

    Args:
        screen: 活动地图 RGB 截图。

    Returns:
        出击按钮匹配结果；未检测到时返回 None。
    """
    return vision.ImageChecker.find_any(
        screen,
        _load_fight_button_templates(),
        roi=constants.FIGHT_BUTTON_ROI,
        confidence=_TEMPLATE_MATCH_CONFIDENCE,
    )


def read_difficulty_icon_state(screen: numpy.ndarray) -> str | None:
    """读取难度切换图标表达的当前难度。

    Args:
        screen: 活动地图 RGB 截图。

    Returns:
        当前难度，H 表示困难，E 表示简单；未检测到时返回 None。
    """
    # 页面显示的是反向切换图标，因此图标类型对应相反的当前难度。
    if (
        vision.ImageChecker.find_any(
            screen,
            _load_difficulty_hard_templates(),
            confidence=_TEMPLATE_MATCH_CONFIDENCE,
        )
        is not None
    ):
        return 'E'
    if (
        vision.ImageChecker.find_any(
            screen,
            _load_difficulty_easy_templates(),
            confidence=_TEMPLATE_MATCH_CONFIDENCE,
        )
        is not None
    ):
        return 'H'
    return None


def read_event_title_match(
    screen: numpy.ndarray,
) -> vision.ImageMatchDetail | None:
    """读取活动地图标题的模板匹配结果。

    Args:
        screen: 活动地图 RGB 截图。

    Returns:
        活动地图标题匹配结果；未检测到时返回 None。
    """
    return vision.ImageChecker.find_any(
        screen,
        _load_event_title_templates(),
        confidence=_TEMPLATE_MATCH_CONFIDENCE,
    )


def read_alpha_entrance_state(screen: numpy.ndarray) -> bool:
    """读取 Alpha 入口是否处于选中状态。

    Args:
        screen: 活动地图 RGB 截图。

    Returns:
        Alpha 入口选中时返回 True。
    """
    pixel = vision.PixelChecker.get_pixel(
        screen,
        *constants.ENTRANCE_ALPHA_PROBE,
    )
    return pixel.near(
        constants.ENTRANCE_ALPHA_COLOR,
        constants.ENTRANCE_ALPHA_TOLERANCE,
    )


# ── 页面模板加载 ─────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _load_fight_button_templates() -> list[vision.ImageTemplate]:
    """延迟加载节点详情浮层的出击按钮模板。"""
    return event.event_fight_button_templates()


@lru_cache(maxsize=1)
def _load_event_title_templates() -> list[vision.ImageTemplate]:
    """延迟加载活动地图标题模板。"""
    return event.event_map_title_templates()


@lru_cache(maxsize=1)
def _load_difficulty_hard_templates() -> list[vision.ImageTemplate]:
    """延迟加载困难模式切换图标模板。"""
    return event.event_difficulty_hard_templates()


@lru_cache(maxsize=1)
def _load_difficulty_easy_templates() -> list[vision.ImageTemplate]:
    """延迟加载简单模式切换图标模板。"""
    return event.event_difficulty_easy_templates()
