"""编排主页公告、每日奖励和确认浮窗的完整子流程。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui import recognition_flow
from autowsgr.application.ui.controller.home.main_page import operations, recognition
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
    overlay: recognition_flow.RecognitionResult[recognition.OverlayMatch],
    *,
    record_screenshot: Callable[[numpy.ndarray], None],
) -> None:
    """处理一个已识别的主页浮窗并确认对应终态。

    Args:
        ctrl: 提供页面操作能力的设备控制器。
        overlay: 公共识别流程返回的浮窗结果。
        record_screenshot: 接收流程中每次截图的 Context 写入回调。

    Raises:
        HomeOverlayError: 浮窗识别结果无效或流程无法确认终态。
    """
    if overlay.value is None:
        raise HomeOverlayError('浮窗识别结果为空')

    if overlay.value.kind is recognition.OverlayKind.NEWS:
        _process_news(ctrl, record_screenshot)
        return

    if overlay.value.kind is recognition.OverlayKind.REWARD:
        confirmation = _process_reward(ctrl, record_screenshot)
    elif overlay.value.kind is recognition.OverlayKind.REWARD_CONFIRM:
        confirmation = overlay
    else:
        raise HomeOverlayError(f'未知浮窗类型: {overlay.value.kind}')

    _confirm_reward(ctrl, confirmation, record_screenshot)


def _process_news(
    ctrl: DeviceService,
    record_screenshot: Callable[[numpy.ndarray], None],
) -> None:
    """处理公告勾选、关闭和终态确认。"""
    _log.info('[UI] 主页 → 处理公告：状态=开始')
    # 1. 识别公告勾选框状态。
    checkbox = recognition_flow.recognize_with_retry(
        ctrl,
        recognition.read_news_checkbox_match,
        record_screenshot=record_screenshot,
    )
    if not checkbox.satisfied or checkbox.value is None:
        raise HomeOverlayError('无法识别公告勾选框状态')

    if not checkbox.value.checked:
        # 2. 未勾选时只点击一次，并等待后续状态确认。
        _log.info('[UI] 主页 → 公告勾选：状态=未勾选，动作=点击')
        operations.click_news_checkbox(
            ctrl,
            recognition.match_center(checkbox.value, checkbox.frame),
        )

    # 3. 重新识别并确认勾选状态。
    checked = recognition_flow.recognize_with_retry(
        ctrl,
        lambda screen: recognition.read_news_checkbox_match(screen, checked=True),
        record_screenshot=record_screenshot,
    )
    if not checked.satisfied:
        raise HomeOverlayError('公告勾选框点击后未确认已勾选')
    _log.info('[UI] 主页 → 公告勾选：结果=已确认')

    # 4. 关闭公告并确认公告消失。
    _log.info('[UI] 主页 → 关闭公告：状态=开始')
    announcement = recognition_flow.recognize_with_retry(
        ctrl,
        recognition.read_news_overlay_match,
        record_screenshot=record_screenshot,
    )
    if not announcement.satisfied:
        raise HomeOverlayError('关闭公告前未确认公告仍处于当前页面')
    operations.click_news_close(ctrl)
    absent = recognition_flow.wait_until_absent(
        ctrl,
        recognition.read_news_overlay_match,
        record_screenshot=record_screenshot,
    )
    if not absent.satisfied:
        raise HomeOverlayError('公告关闭后仍然存在，停止重复点击')
    _log.info('[UI] 主页 → 关闭公告：结果=成功')


def _process_reward(
    ctrl: DeviceService,
    record_screenshot: Callable[[numpy.ndarray], None],
) -> recognition_flow.RecognitionResult[recognition.OverlayMatch]:
    """识别并点击每日奖励领取按钮。"""
    _log.info('[UI] 主页 → 领取每日奖励：状态=开始')
    # 1. 识别领取按钮后点击一次。
    claim = recognition_flow.recognize_with_retry(
        ctrl,
        recognition.read_reward_claim_match,
        record_screenshot=record_screenshot,
    )
    if not claim.satisfied or claim.value is None:
        raise HomeOverlayError('无法识别每日奖励领取按钮')
    operations.click_reward_claim(
        ctrl,
        recognition.match_center(claim.value, claim.frame),
    )

    # 2. 识别确认浮窗并返回确认按钮。
    confirmation = recognition_flow.recognize_with_retry(
        ctrl,
        recognition.read_reward_confirmation_match,
        record_screenshot=record_screenshot,
    )
    if not confirmation.satisfied:
        raise HomeOverlayError('领取奖励后未出现确认浮窗')
    return confirmation


def _confirm_reward(
    ctrl: DeviceService,
    confirmation: recognition_flow.RecognitionResult[recognition.OverlayMatch],
    record_screenshot: Callable[[numpy.ndarray], None],
) -> None:
    """点击奖励确认按钮并确认确认浮窗消失。"""
    if confirmation.value is None:
        raise HomeOverlayError('奖励确认浮窗识别结果为空')

    # 1. 点击已经识别出的确认按钮。
    _log.info('[UI] 主页 → 确认奖励：状态=开始')
    operations.click_reward_confirmation(
        ctrl,
        recognition.match_center(confirmation.value, confirmation.frame),
    )
    absent = recognition_flow.wait_until_absent(
        ctrl,
        recognition.read_reward_confirmation_match,
        record_screenshot=record_screenshot,
    )
    if not absent.satisfied:
        raise HomeOverlayError('确认按钮点击后仍然存在，停止重复点击')
    _log.info('[UI] 主页 → 确认奖励：结果=成功')
    _log.info('[UI] 主页 → 领取每日奖励：结果=成功')


__all__ = ['HomeOverlayError', 'handle_overlay']
