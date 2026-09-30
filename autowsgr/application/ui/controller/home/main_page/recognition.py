"""识别主页浮窗和通知事实。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home.main_page import constants
from autowsgr.common import vision
from autowsgr.common.vision.config import (
    OPENCV_TEMPLATE_SOURCE_RESOLUTION,
)
from autowsgr.common.vision.operations.template_matching import (
    Template,
    TemplateMatchResult,
)


if TYPE_CHECKING:
    from collections.abc import Sequence

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
NEWS_TEMPLATE = 'HOME_NEWS_TEXT_720P.png'
NEWS_CHECKED_TEMPLATE = 'HOME_NEWS_CHECKBOX_CHECKED_720P.png'
NEWS_UNCHECKED_TEMPLATE = 'HOME_NEWS_CHECKBOX_UNCHECKED_720P.png'
REWARD_TEMPLATE = 'HOME_REWARD_TEXT_720P.png'
REWARD_CLAIM_TEMPLATE = 'HOME_REWARD_CLAIM_BUTTON_720P.png'
CONFIRM_TEMPLATE = 'HOME_REWARD_CONFIRM_BUTTON_720P.png'
_OVERLAY_KIND_BY_TEMPLATE = {
    NEWS_TEMPLATE: OverlayKind.NEWS,
    REWARD_TEMPLATE: OverlayKind.REWARD,
    CONFIRM_TEMPLATE: OverlayKind.REWARD_CONFIRM,
}


@cache
def load_template(filename: str) -> Template:
    """从主页模块资源目录加载一个模板。"""
    path = f'{_TEMPLATE_PREFIX}{filename}'
    return Template(
        name=path.rsplit('/', 1)[-1].removesuffix('.png'),
        relative_path=path,
        image=vision.opencv.load_image(path),
        source_resolution=OPENCV_TEMPLATE_SOURCE_RESOLUTION,
    )


def read_overlay_match(
    results: TemplateMatchResult | Sequence[TemplateMatchResult],
) -> OverlayMatch | None:
    """按公共识别流的结果顺序读取第一个浮窗事实。"""
    for result in _as_results(results):
        match = _overlay_match(result)
        if match is not None:
            return match
    return None


def read_news_overlay_match(
    results: TemplateMatchResult | Sequence[TemplateMatchResult],
) -> OverlayMatch | None:
    """从公共识别流的模板结果中读取公告浮窗事实。"""
    for result in _as_results(results):
        match = _overlay_match(result)
        if match is not None and match.kind is OverlayKind.NEWS:
            return match
    return None


def read_news_checkbox_match(
    results: TemplateMatchResult | Sequence[TemplateMatchResult],
) -> CheckboxMatch | None:
    """从公共识别流的模板结果中选取置信度最高的勾选框状态。"""
    matches: list[CheckboxMatch] = []
    for result in _as_results(results):
        filename = result.template_path.rsplit('/', 1)[-1]
        if not result.matched or filename not in (NEWS_CHECKED_TEMPLATE, NEWS_UNCHECKED_TEMPLATE):
            continue
        matches.append(
            CheckboxMatch(
                filename == NEWS_CHECKED_TEMPLATE,
                load_template(filename),
                result,
            ),
        )
    return max(matches, key=lambda item: item.result.score, default=None)


def read_reward_claim_match(result: TemplateMatchResult) -> OverlayMatch | None:
    """从公共识别流的模板结果中读取每日奖励领取按钮。"""
    if not result.matched or result.template_path.rsplit('/', 1)[-1] != REWARD_CLAIM_TEMPLATE:
        return None
    return OverlayMatch(OverlayKind.REWARD, load_template(REWARD_CLAIM_TEMPLATE), result)


def read_reward_confirmation_match(result: TemplateMatchResult) -> OverlayMatch | None:
    """从公共识别流的模板结果中读取奖励确认按钮。"""
    if not result.matched or result.template_path.rsplit('/', 1)[-1] != CONFIRM_TEMPLATE:
        return None
    return OverlayMatch(OverlayKind.REWARD_CONFIRM, load_template(CONFIRM_TEMPLATE), result)


def read_overlay(
    results: TemplateMatchResult | Sequence[TemplateMatchResult],
) -> OverlayKind | None:
    """从公共识别流的模板结果中读取当前主页浮窗类型。"""
    match = read_overlay_match(results)
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


def _overlay_match(result: TemplateMatchResult) -> OverlayMatch | None:
    """把已命中的主页浮窗模板结果转换为浮窗事实。"""
    filename = result.template_path.rsplit('/', 1)[-1]
    kind = _OVERLAY_KIND_BY_TEMPLATE.get(filename)
    if not result.matched or kind is None:
        return None
    return OverlayMatch(kind, load_template(filename), result)


def _as_results(
    results: TemplateMatchResult | Sequence[TemplateMatchResult],
) -> Sequence[TemplateMatchResult]:
    """统一单张和多张模板匹配结果的遍历方式。"""
    return (results,) if isinstance(results, TemplateMatchResult) else results


__all__ = [
    'CONFIRM_TEMPLATE',
    'NEWS_CHECKED_TEMPLATE',
    'NEWS_TEMPLATE',
    'NEWS_UNCHECKED_TEMPLATE',
    'REWARD_CLAIM_TEMPLATE',
    'REWARD_TEMPLATE',
    'CheckboxMatch',
    'OverlayKind',
    'OverlayMatch',
    'check_expedition_ready',
    'check_task_ready',
    'load_template',
    'match_center',
    'read_news_checkbox_match',
    'read_news_overlay_match',
    'read_overlay',
    'read_overlay_match',
    'read_reward_claim_match',
    'read_reward_confirmation_match',
]
