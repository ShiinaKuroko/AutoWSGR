"""验证 UI 公共识别流程的截图、重试和终态契约。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from autowsgr.application.ui import recognition_flow


def test_capture_frame_records_the_returned_frame() -> None:
    """截图流程只调用设备一次，并把同一帧交给调用方回调。"""
    frame = np.zeros((2, 2, 3), dtype=np.uint8)
    ctrl = SimpleNamespace(screenshot=MagicMock(return_value=frame))
    recorder = MagicMock()

    result = recognition_flow.capture_frame(ctrl, record_screenshot=recorder)

    assert result is frame
    recorder.assert_called_once_with(frame)


def test_recognize_with_retry_returns_the_first_match(monkeypatch: object) -> None:
    """正向识别失败后按间隔重试，并返回命中的值和帧。"""
    frames = [np.zeros((1, 1, 3), dtype=np.uint8) for _ in range(2)]
    ctrl = SimpleNamespace(screenshot=MagicMock(side_effect=frames))
    recorder = MagicMock()
    sleep = MagicMock()
    monkeypatch.setattr(recognition_flow.time, 'sleep', sleep)

    result = recognition_flow.recognize_with_retry(
        ctrl,
        lambda frame: 'matched' if frame is frames[1] else False,
        record_screenshot=recorder,
    )

    assert result.matched is True
    assert result.satisfied is True
    assert result.value == 'matched'
    assert result.frame is frames[1]
    assert result.attempts == 2
    assert recorder.call_count == 2
    sleep.assert_called_once_with(0.5)


def test_recognize_with_retry_retries_structured_false_results(
    monkeypatch: object,
) -> None:
    """模板或像素结构结果的 matched=False 必须继续重试。"""
    frames = [np.zeros((1, 1, 3), dtype=np.uint8) for _ in range(2)]
    ctrl = SimpleNamespace(screenshot=MagicMock(side_effect=frames))
    recorder = MagicMock()
    monkeypatch.setattr(recognition_flow.time, 'sleep', MagicMock())

    result = recognition_flow.recognize_with_retry(
        ctrl,
        lambda _frame: SimpleNamespace(matched=False),
        record_screenshot=recorder,
        attempts=2,
        interval_seconds=0,
    )

    assert result.satisfied is False
    assert result.attempts == 2


def test_recognize_with_retry_retries_empty_ocr_results() -> None:
    """空 OCR 结果必须被视为未命中。"""
    frame = np.zeros((1, 1, 3), dtype=np.uint8)
    ctrl = SimpleNamespace(screenshot=MagicMock(return_value=frame))

    result = recognition_flow.recognize_with_retry(
        ctrl,
        lambda _frame: [],
        record_screenshot=MagicMock(),
        attempts=1,
        interval_seconds=0,
    )

    assert result.satisfied is False


def test_wait_until_absent_accepts_unmatched_structured_results() -> None:
    """目标结构结果明确未命中时，终态确认应立即成功。"""
    frame = np.zeros((1, 1, 3), dtype=np.uint8)
    ctrl = SimpleNamespace(screenshot=MagicMock(return_value=frame))

    result = recognition_flow.wait_until_absent(
        ctrl,
        lambda _frame: SimpleNamespace(matched=False),
        record_screenshot=MagicMock(),
        attempts=1,
        interval_seconds=0,
    )

    assert result.satisfied is True
    assert result.matched is False


def test_capture_frame_requires_context_recorder() -> None:
    """公共截图流程禁止静默跳过 Context 写入。"""
    ctrl = SimpleNamespace(screenshot=MagicMock())

    with pytest.raises(TypeError):
        recognition_flow.capture_frame(ctrl)
    with pytest.raises(TypeError):
        recognition_flow.capture_frame(ctrl, record_screenshot=None)


def test_wait_until_absent_reports_failure_when_target_remains(
    monkeypatch: object,
) -> None:
    """目标持续存在三次时返回失败结果，不在公共层抛业务异常。"""
    ctrl = SimpleNamespace(
        screenshot=MagicMock(
            side_effect=[np.zeros((1, 1, 3), dtype=np.uint8) for _ in range(3)],
        ),
    )
    sleep = MagicMock()
    monkeypatch.setattr(recognition_flow.time, 'sleep', sleep)
    recorder = MagicMock()

    result = recognition_flow.wait_until_absent(
        ctrl,
        lambda _frame: 'still-present',
        record_screenshot=recorder,
    )

    assert result.matched is True
    assert result.satisfied is False
    assert result.value == 'still-present'
    assert result.attempts == 3
    assert sleep.call_count == 2
