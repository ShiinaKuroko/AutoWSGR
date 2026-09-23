"""识别主页浮窗和通知事实。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home.main_page import constants
from autowsgr.common import vision
from autowsgr.common.vision.config import (
    OPENCV_TEMPLATE_CONFIDENCE,
    OPENCV_TEMPLATE_SOURCE_RESOLUTION,
)
from autowsgr.common.vision.operations.template_matching import (
    ROI,
    Template,
    TemplateMatchResult,
)


if TYPE_CHECKING:
    import numpy as np


class OverlayKind(StrEnum):
    """按主页处理顺序定义的浮窗类型。"""

    NEWS = 'news'
    REWARD_CONFIRM = 'reward_confirm'
    REWARD = 'reward'


@dataclass(frozen=True, slots=True)
class OverlayMatch:
    """保存已匹配的浮窗类型、模板和匹配结果。"""

    kind: OverlayKind
    template: Template
    result: TemplateMatchResult

    @property
    def score(self) -> float:
        """返回模板匹配置信度。"""
        return self.result.score


@dataclass(frozen=True, slots=True)
class CheckboxMatch:
    """保存公告勾选状态、模板和匹配结果。"""

    checked: bool
    template: Template
    result: TemplateMatchResult


_TEMPLATE_PREFIX = 'application/ui/controller/home/main_page/'
_NEWS_TEMPLATE = 'HOME_NEWS_TEXT_720P.png'
_NEWS_CHECKED_TEMPLATE = 'HOME_NEWS_CHECKBOX_CHECKED_720P.png'
_NEWS_UNCHECKED_TEMPLATE = 'HOME_NEWS_CHECKBOX_UNCHECKED_720P.png'
_REWARD_TEMPLATE = 'HOME_REWARD_TEXT_720P.png'
_REWARD_CLAIM_TEMPLATE = 'HOME_REWARD_CLAIM_BUTTON_720P.png'
_CONFIRM_TEMPLATE = 'HOME_REWARD_CONFIRM_BUTTON_720P.png'


@cache
def _load_template(filename: str, source_resolution: tuple[int, int]) -> Template:
    """从主页模块资源目录加载一个模板。"""
    path = f'{_TEMPLATE_PREFIX}{filename}'
    return Template(
        name=path.rsplit('/', 1)[-1].removesuffix('.png'),
        relative_path=path,
        image=vision.opencv.load_image(path),
        source_resolution=source_resolution,
    )


def _match_template(
    screen: np.ndarray,
    filename: str,
    roi: ROI,
    kind: OverlayKind,
) -> OverlayMatch | None:
    """匹配一个主页模板并转换为浮窗事实。"""
    template = _load_template(filename, OPENCV_TEMPLATE_SOURCE_RESOLUTION)
    result = vision.match_template(
        screen,
        template,
        roi=roi,
        confidence=OPENCV_TEMPLATE_CONFIDENCE,
    )
    if not result.matched:
        return None
    return OverlayMatch(kind, template, result)


def read_overlay_match(
    screen: np.ndarray,
) -> OverlayMatch | None:
    """按公告、奖励、确认顺序读取第一个浮窗事实。"""
    candidates = (
        (_NEWS_TEMPLATE, constants.NEWS_TEXT_ROI, OverlayKind.NEWS),
        (_REWARD_TEMPLATE, constants.REWARD_TEXT_ROI, OverlayKind.REWARD),
        (_CONFIRM_TEMPLATE, constants.REWARD_CONFIRM_BUTTON_ROI, OverlayKind.REWARD_CONFIRM),
    )
    for filename, roi, kind in candidates:
        match = _match_template(screen, filename, roi, kind)
        if match is not None:
            return match
    return None


def read_news_overlay_match(screen: np.ndarray) -> OverlayMatch | None:
    """读取当前公告浮窗事实，用于公告关闭后的终态确认。"""
    match = read_overlay_match(screen)
    if match is not None and match.kind is OverlayKind.NEWS:
        return match
    return None


def read_news_checkbox_match(
    screen: np.ndarray,
    *,
    checked: bool | None = None,
) -> CheckboxMatch | None:
    """识别公告勾选框状态和点击目标。"""
    candidates = ((True, _NEWS_CHECKED_TEMPLATE), (False, _NEWS_UNCHECKED_TEMPLATE))
    if checked is not None:
        candidates = tuple(item for item in candidates if item[0] is checked)

    matches: list[CheckboxMatch] = []
    for state, path in candidates:
        template = _load_template(path, OPENCV_TEMPLATE_SOURCE_RESOLUTION)
        result = vision.match_template(
            screen,
            template,
            roi=constants.NEWS_CHECKBOX_ROI,
            confidence=OPENCV_TEMPLATE_CONFIDENCE,
        )
        if result.matched:
            matches.append(CheckboxMatch(state, template, result))
    return max(matches, key=lambda item: item.result.score, default=None)


def read_reward_claim_match(screen: np.ndarray) -> OverlayMatch | None:
    """识别每日奖励领取按钮。"""
    return _match_template(
        screen,
        _REWARD_CLAIM_TEMPLATE,
        constants.REWARD_CLAIM_BUTTON_ROI,
        OverlayKind.REWARD,
    )


def read_reward_confirmation_match(screen: np.ndarray) -> OverlayMatch | None:
    """识别当前奖励确认按钮。"""
    return _match_template(
        screen,
        _CONFIRM_TEMPLATE,
        constants.REWARD_CONFIRM_BUTTON_ROI,
        OverlayKind.REWARD_CONFIRM,
    )


def read_overlay(
    screen: np.ndarray,
) -> OverlayKind | None:
    """读取当前主页浮窗类型，没有浮窗时返回 ``None``。"""
    match = read_overlay_match(screen)
    return match.kind if match is not None else None


def match_center(match: OverlayMatch | CheckboxMatch, screen: np.ndarray) -> tuple[float, float]:
    """将模板匹配位置转换为归一化点击中心。"""
    if match.result.location is None:
        raise ValueError('模板匹配结果缺少位置')
    height, width = screen.shape[:2]
    source_width, source_height = match.template.source_resolution
    scale_x = width / source_width
    scale_y = height / source_height
    template_height, template_width = match.template.image.shape[:2]
    x, y = match.result.location
    center_x = (x + template_width * scale_x / 2) / width
    center_y = (y + template_height * scale_y / 2) / height
    return center_x, center_y


def check_expedition_ready(screen: np.ndarray) -> bool:
    """检查远征完成通知颜色是否出现。"""
    return _check_notification(screen, 'expedition_ready')


def check_task_ready(screen: np.ndarray) -> bool:
    """检查任务奖励通知颜色是否出现。"""
    return _check_notification(screen, 'task_ready')


def _check_notification(screen: np.ndarray, name: str) -> bool:
    """检查一个命名主页通知探针。"""
    pixel = vision.numpy.sample_pixel(screen, *constants.PROBE_POSITIONS[name])
    return constants.NOTIFICATION_RED.near(
        type(constants.NOTIFICATION_RED)(*pixel),
        constants.NOTIFICATION_RED_TOLERANCE,
    )


__all__ = [
    'CheckboxMatch',
    'OverlayKind',
    'OverlayMatch',
    'check_expedition_ready',
    'check_task_ready',
    'match_center',
    'read_news_checkbox_match',
    'read_news_overlay_match',
    'read_overlay',
    'read_overlay_match',
    'read_reward_claim_match',
    'read_reward_confirmation_match',
]
