"""主页浮窗状态迁移测试。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import numpy as np

from autowsgr.application.ui import recognition_flow
from autowsgr.application.ui.controller.home.main_page import operations, recognition
from autowsgr.application.ui.controller.home.main_page import page as page_module
from autowsgr.common.vision.operations.template_matching import TemplateMatchResult


if TYPE_CHECKING:
    import pytest


_TEMPLATE_ROOT = 'application/ui/controller/home/main_page'


def _template_result(filename: str, matched: bool) -> TemplateMatchResult:
    return TemplateMatchResult(
        matched=matched,
        score=0.9 if matched else 0.2,
        location=(10, 10) if matched else None,
        template_path=f'{_TEMPLATE_ROOT}/{filename}',
    )


def _flow_result(
    frame: np.ndarray,
    value: object,
    matched: bool,
) -> recognition_flow.RecognitionResult[object]:
    return recognition_flow.RecognitionResult(matched, matched, value, frame, 1)


def _prepare_page(
    monkeypatch: pytest.MonkeyPatch,
    flow_results: list[object],
) -> tuple[page_module.HomePage, np.ndarray, list[dict[str, object]]]:
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    ctrl = SimpleNamespace(screenshot=MagicMock())
    page = page_module.HomePage(SimpleNamespace(ctrl=ctrl, record_screenshot=MagicMock()))
    flow_calls: list[dict[str, object]] = []

    def recognize(_ctrl: object, **kwargs: object) -> object:
        flow_calls.append(kwargs)
        return flow_results.pop(0)

    monkeypatch.setattr(page_module.recognition_flow, 'recognize_with_retry', recognize)
    monkeypatch.setattr(
        page_module.recognition_flow,
        'wait_until_absent',
        MagicMock(
            return_value=recognition_flow.RecognitionResult(
                False,
                True,
                _template_result(recognition.NEWS_TEMPLATE, False),
                frame,
                1,
            ),
        ),
    )
    monkeypatch.setattr(
        recognition,
        'load_template',
        lambda filename: SimpleNamespace(name=filename, image=frame, source_resolution=(1280, 720)),
    )
    monkeypatch.setattr(recognition, 'match_center', MagicMock(return_value=(0.5, 0.5)))
    return page, frame, flow_calls


def test_home_page_checks_checkbox_before_closing_news(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """公告流程通过公共 OpenCV 模式识别勾选框、关闭并确认消失。"""
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    no_overlay = (
        _template_result(recognition.NEWS_TEMPLATE, False),
        _template_result(recognition.REWARD_TEMPLATE, False),
        _template_result(recognition.CONFIRM_TEMPLATE, False),
    )
    flow_results = [
        _flow_result(frame, (_template_result(recognition.NEWS_TEMPLATE, True),), True),
        _flow_result(
            frame,
            (
                _template_result(recognition.NEWS_CHECKED_TEMPLATE, False),
                _template_result(recognition.NEWS_UNCHECKED_TEMPLATE, True),
            ),
            True,
        ),
        _flow_result(frame, _template_result(recognition.NEWS_CHECKED_TEMPLATE, True), True),
        _flow_result(frame, _template_result(recognition.NEWS_TEMPLATE, True), True),
        _flow_result(frame, no_overlay, False),
    ]
    page, _, flow_calls = _prepare_page(monkeypatch, flow_results)
    click_checkbox = MagicMock()
    click_close = MagicMock()
    monkeypatch.setattr(operations, 'click_news_checkbox', click_checkbox)
    monkeypatch.setattr(operations, 'click_news_close', click_close)

    assert page.dismiss_current_overlay() is True
    assert len(flow_calls) == 5
    assert all(call['mode'] is recognition_flow.RecognitionMode.OPENCV for call in flow_calls)
    assert len(flow_calls[0]['template']) == 3
    click_checkbox.assert_called_once()
    click_close.assert_called_once_with(page._ctrl)


def test_home_page_claims_reward_and_verifies_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """奖励流程使用公共 OpenCV 结果点击领取和确认按钮。"""
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    no_overlay = (
        _template_result(recognition.NEWS_TEMPLATE, False),
        _template_result(recognition.REWARD_TEMPLATE, False),
        _template_result(recognition.CONFIRM_TEMPLATE, False),
    )
    flow_results = [
        _flow_result(frame, (_template_result(recognition.REWARD_TEMPLATE, True),), True),
        _flow_result(frame, _template_result(recognition.REWARD_CLAIM_TEMPLATE, True), True),
        _flow_result(frame, _template_result(recognition.CONFIRM_TEMPLATE, True), True),
        _flow_result(frame, no_overlay, False),
    ]
    page, _, flow_calls = _prepare_page(monkeypatch, flow_results)
    click_claim = MagicMock()
    click_confirmation = MagicMock()
    monkeypatch.setattr(operations, 'click_reward_claim', click_claim)
    monkeypatch.setattr(operations, 'click_reward_confirmation', click_confirmation)

    assert page.dismiss_current_overlay() is True
    assert len(flow_calls) == 4
    assert all(call['mode'] is recognition_flow.RecognitionMode.OPENCV for call in flow_calls)
    click_claim.assert_called_once()
    click_confirmation.assert_called_once()
