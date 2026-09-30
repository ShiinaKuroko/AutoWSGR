"""编排主页公告、每日奖励和确认浮窗的完整子流程。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui import recognition_flow
from autowsgr.application.ui.controller.home.main_page import constants, operations, recognition
from autowsgr.common.system.errors import ApplicationError
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy

    from autowsgr.common.device.service import DeviceService


_log = get_logger('ui.home.main_page.workflow')


class HomeOverlayError(ApplicationError):
    """主页浮窗子流程无法到达终态时抛出。"""


def handle_overlay(
    ctrl: DeviceService,
    overlay: recognition.OverlayMatch,
    frame: numpy.ndarray,
    *,
    record_screenshot: Callable[[numpy.ndarray], None],
) -> None:
    """处理一个已识别的主页浮窗并确认对应终态。"""
    if overlay.kind is recognition.OverlayKind.NEWS:
        _process_news(ctrl, record_screenshot)
        return

    if overlay.kind is recognition.OverlayKind.REWARD:
        confirmation, confirmation_frame = _process_reward(ctrl, record_screenshot)
    elif overlay.kind is recognition.OverlayKind.REWARD_CONFIRM:
        confirmation, confirmation_frame = overlay, frame
    else:
        raise HomeOverlayError(f'未知浮窗类型: {overlay.kind}')

    _confirm_reward(ctrl, confirmation, confirmation_frame, record_screenshot)


def _process_news(
    ctrl: DeviceService,
    record_screenshot: Callable[[numpy.ndarray], None],
) -> None:
    """处理公告勾选、关闭和终态确认。"""
    _log.info('[UI] 主页 → 处理公告：状态=开始')
    checkbox_templates = (
        recognition.load_template(recognition.NEWS_CHECKED_TEMPLATE),
        recognition.load_template(recognition.NEWS_UNCHECKED_TEMPLATE),
    )
    checkbox = recognition_flow.recognize_with_retry(
        ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=checkbox_templates,
        roi=constants.NEWS_CHECKBOX_ROI,
        record_screenshot=record_screenshot,
    )
    checkbox_match = recognition.read_news_checkbox_match(checkbox.value)
    if not checkbox.satisfied or checkbox_match is None:
        raise HomeOverlayError('无法识别公告勾选框状态')

    if not checkbox_match.checked:
        _log.info('[UI] 主页 → 公告勾选：状态=未勾选，动作=点击')
        operations.click_news_checkbox(
            ctrl,
            recognition.match_center(checkbox_match, checkbox.frame),
        )

    checked_template = recognition.load_template(recognition.NEWS_CHECKED_TEMPLATE)
    checked = recognition_flow.recognize_with_retry(
        ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=checked_template,
        roi=constants.NEWS_CHECKBOX_ROI,
        record_screenshot=record_screenshot,
    )
    checked_match = recognition.read_news_checkbox_match(checked.value)
    if not checked.satisfied or checked_match is None or not checked_match.checked:
        raise HomeOverlayError('公告勾选框点击后未确认已勾选')
    _log.info('[UI] 主页 → 公告勾选：结果=已确认')

    _log.info('[UI] 主页 → 关闭公告：状态=开始')
    news_template = recognition.load_template(recognition.NEWS_TEMPLATE)
    announcement = recognition_flow.recognize_with_retry(
        ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=news_template,
        roi=constants.NEWS_TEXT_ROI,
        record_screenshot=record_screenshot,
    )
    announcement_match = recognition.read_news_overlay_match(announcement.value)
    if not announcement.satisfied or announcement_match is None:
        raise HomeOverlayError('关闭公告前未确认公告仍处于当前页面')
    operations.click_news_close(ctrl)
    absent = recognition_flow.wait_until_absent(
        ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=news_template,
        roi=constants.NEWS_TEXT_ROI,
        record_screenshot=record_screenshot,
    )
    if not absent.satisfied:
        raise HomeOverlayError('公告关闭后仍然存在，停止重复点击')
    _log.info('[UI] 主页 → 关闭公告：结果=成功')


def _process_reward(
    ctrl: DeviceService,
    record_screenshot: Callable[[numpy.ndarray], None],
) -> tuple[recognition.OverlayMatch, numpy.ndarray]:
    """识别并点击每日奖励领取按钮。"""
    _log.info('[UI] 主页 → 领取每日奖励：状态=开始')
    claim_template = recognition.load_template(recognition.REWARD_CLAIM_TEMPLATE)
    claim = recognition_flow.recognize_with_retry(
        ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=claim_template,
        roi=constants.REWARD_CLAIM_BUTTON_ROI,
        record_screenshot=record_screenshot,
    )
    claim_match = recognition.read_reward_claim_match(claim.value)
    if not claim.satisfied or claim_match is None:
        raise HomeOverlayError('无法识别每日奖励领取按钮')
    operations.click_reward_claim(
        ctrl,
        recognition.match_center(claim_match, claim.frame),
    )

    confirmation_template = recognition.load_template(recognition.CONFIRM_TEMPLATE)
    confirmation = recognition_flow.recognize_with_retry(
        ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=confirmation_template,
        roi=constants.REWARD_CONFIRM_BUTTON_ROI,
        record_screenshot=record_screenshot,
    )
    confirmation_match = recognition.read_reward_confirmation_match(confirmation.value)
    if not confirmation.satisfied or confirmation_match is None:
        raise HomeOverlayError('领取奖励后未出现确认浮窗')
    return confirmation_match, confirmation.frame


def _confirm_reward(
    ctrl: DeviceService,
    confirmation: recognition.OverlayMatch,
    frame: numpy.ndarray,
    record_screenshot: Callable[[numpy.ndarray], None],
) -> None:
    """点击奖励确认按钮并确认确认浮窗消失。"""
    _log.info('[UI] 主页 → 确认奖励：状态=开始')
    operations.click_reward_confirmation(
        ctrl,
        recognition.match_center(confirmation, frame),
    )
    absent = recognition_flow.wait_until_absent(
        ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=recognition.load_template(recognition.CONFIRM_TEMPLATE),
        roi=constants.REWARD_CONFIRM_BUTTON_ROI,
        record_screenshot=record_screenshot,
    )
    if not absent.satisfied:
        raise HomeOverlayError('确认按钮点击后仍然存在，停止重复点击')
    _log.info('[UI] 主页 → 确认奖励：结果=成功')
    _log.info('[UI] 主页 → 领取每日奖励：结果=成功')


__all__ = ['HomeOverlayError', 'handle_overlay']
