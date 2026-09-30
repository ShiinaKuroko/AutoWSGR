"""验证 UI 公共识别流程的模式分发、截图和终态契约。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from autowsgr.application.ui import recognition_flow
from autowsgr.common.vision.operations.pixel_matching import Color, PixelRule, PixelSignature
from autowsgr.common.vision.operations.template_matching import ROI, Template


def _template(name: str) -> Template:
    """构造最小模板输入。"""
    return Template(name, f'{name}.png', np.zeros((1, 1, 3), dtype=np.uint8))


def test_capture_frame_records_the_returned_frame() -> None:
    """截图流程只调用设备一次，并把同一帧交给调用方回调。"""
    frame = np.zeros((2, 2, 3), dtype=np.uint8)
    ctrl = SimpleNamespace(screenshot=MagicMock(return_value=frame))
    recorder = MagicMock()

    result = recognition_flow.capture_frame(ctrl, record_screenshot=recorder)

    assert result is frame
    recorder.assert_called_once_with(frame)


def test_opencv_retry_matches_the_recorded_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenCV 收到写入 Context 的同一帧，并在首次命中时停止重试。"""
    frames = [np.zeros((1, 1, 3), dtype=np.uint8) for _ in range(2)]
    ctrl = SimpleNamespace(screenshot=MagicMock(side_effect=frames))
    template = _template('home')
    roi = ROI(0.1, 0.1, 0.9, 0.9)
    events: list[str] = []
    matches = iter((SimpleNamespace(matched=False), SimpleNamespace(matched=True)))

    def record(frame: np.ndarray) -> None:
        events.append('record')
        assert frame is frames[len(events) // 2]

    def match_template(
        frame: np.ndarray,
        actual_template: Template,
        *,
        roi: ROI,
        confidence: float,
    ) -> SimpleNamespace:
        events.append('match')
        assert frame is frames[(len(events) - 1) // 2]
        assert actual_template is template
        assert roi is not None
        assert confidence == 0.85
        return next(matches)

    monkeypatch.setattr(recognition_flow.vision, 'match_template', match_template)
    monkeypatch.setattr(recognition_flow.time, 'sleep', MagicMock())

    result = recognition_flow.recognize_with_retry(
        ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=template,
        roi=roi,
        record_screenshot=record,
        attempts=2,
        interval_seconds=0,
    )

    assert result.satisfied is True
    assert result.value.matched is True
    assert result.frame is frames[1]
    assert result.attempts == 2
    assert events == ['record', 'match', 'record', 'match']


def test_opencv_matches_each_template_with_its_roi(monkeypatch: pytest.MonkeyPatch) -> None:
    """多模板默认按任一命中判断，并保留输入顺序和各自 ROI。"""
    frame = np.zeros((1, 1, 3), dtype=np.uint8)
    ctrl = SimpleNamespace(screenshot=MagicMock(return_value=frame))
    templates = (_template('one'), _template('two'), _template('three'))
    rois = (ROI(0.0, 0.0, 0.2, 0.2), ROI(0.2, 0.0, 0.4, 0.2), ROI(0.4, 0.0, 0.6, 0.2))
    observed: list[tuple[Template, ROI]] = []
    results = iter(
        (
            SimpleNamespace(matched=True),
            SimpleNamespace(matched=False),
            SimpleNamespace(matched=False),
        ),
    )

    def match_template(
        image: np.ndarray,
        template: Template,
        *,
        roi: ROI,
        confidence: float,
    ) -> SimpleNamespace:
        assert image is frame
        assert confidence == 0.85
        observed.append((template, roi))
        return next(results)

    monkeypatch.setattr(recognition_flow.vision, 'match_template', match_template)

    result = recognition_flow.recognize_with_retry(
        ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=templates,
        roi=rois,
        record_screenshot=MagicMock(),
        attempts=1,
        interval_seconds=0,
    )

    assert result.satisfied is True
    assert [item[0] for item in observed] == list(templates)
    assert [item[1] for item in observed] == list(rois)
    assert [item.matched for item in result.value] == [True, False, False]


def test_ocr_mode_passes_the_recorded_frame_and_options(monkeypatch: pytest.MonkeyPatch) -> None:
    """OCR 模式把帧和文字识别参数交给 common.vision.ocr。"""
    frame = np.zeros((1, 1, 3), dtype=np.uint8)
    ctrl = SimpleNamespace(screenshot=MagicMock(return_value=frame))
    roi = ROI(0.1, 0.2, 0.8, 0.9)
    detections = [object()]
    ocr = MagicMock(return_value=detections)
    monkeypatch.setattr(recognition_flow.vision, 'ocr', ocr)

    result = recognition_flow.recognize_with_retry(
        ctrl,
        mode=recognition_flow.RecognitionMode.OCR,
        roi=roi,
        allowlist='0123456789',
        recognition_profile='single_line',
        candidates=('3', '10'),
        record_screenshot=MagicMock(),
        attempts=1,
        interval_seconds=0,
    )

    assert result.satisfied is True
    assert result.value is detections
    ocr.assert_called_once_with(
        frame,
        roi=roi,
        allowlist='0123456789',
        recognition_profile='single_line',
        candidates=('3', '10'),
    )


def test_numpy_mode_passes_the_pixel_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    """NumPy 模式把签名、ROI 和详情选项交给 common.vision.match_pixels。"""
    frame = np.zeros((1, 1, 3), dtype=np.uint8)
    ctrl = SimpleNamespace(screenshot=MagicMock(return_value=frame))
    roi = ROI(0.1, 0.2, 0.8, 0.9)
    signature = PixelSignature('sample', (PixelRule(0.5, 0.5, Color(10, 20, 30)),))
    pixel_result = SimpleNamespace(matched=True)
    match_pixels = MagicMock(return_value=pixel_result)
    monkeypatch.setattr(recognition_flow.vision, 'match_pixels', match_pixels)

    result = recognition_flow.recognize_with_retry(
        ctrl,
        mode=recognition_flow.RecognitionMode.NUMPY,
        signature=signature,
        roi=roi,
        with_details=True,
        record_screenshot=MagicMock(),
        attempts=1,
        interval_seconds=0,
    )

    assert result.satisfied is True
    assert result.value is pixel_result
    match_pixels.assert_called_once_with(frame, signature, roi=roi, with_details=True)


def test_wait_until_absent_accepts_empty_ocr_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """OCR 返回空结果時，终态确认立即判定目标已消失。"""
    frame = np.zeros((1, 1, 3), dtype=np.uint8)
    ctrl = SimpleNamespace(screenshot=MagicMock(return_value=frame))
    ocr = MagicMock(return_value=[])
    monkeypatch.setattr(recognition_flow.vision, 'ocr', ocr)

    result = recognition_flow.wait_until_absent(
        ctrl,
        mode=recognition_flow.RecognitionMode.OCR,
        record_screenshot=MagicMock(),
        attempts=1,
        interval_seconds=0,
    )

    assert result.satisfied is True
    assert result.matched is False
    assert result.value == []
    ocr.assert_called_once_with(
        frame,
        roi=None,
        allowlist='',
        recognition_profile='full',
        candidates=None,
    )


def test_mode_inputs_are_validated_before_screenshot() -> None:
    """错误模式输入在设备 IO 前失败。"""
    ctrl = SimpleNamespace(screenshot=MagicMock())

    with pytest.raises(ValueError, match='unknown'):
        recognition_flow.recognize_with_retry(
            ctrl,
            mode='unknown',
            record_screenshot=MagicMock(),
        )
    with pytest.raises(ValueError, match='OpenCV'):
        recognition_flow.recognize_with_retry(
            ctrl,
            mode=recognition_flow.RecognitionMode.OPENCV,
            record_screenshot=MagicMock(),
        )

    ctrl.screenshot.assert_not_called()


def test_capture_frame_requires_context_recorder() -> None:
    """公共截图流程禁止静默跳过 Context 写入。"""
    ctrl = SimpleNamespace(screenshot=MagicMock())

    with pytest.raises(TypeError):
        recognition_flow.capture_frame(ctrl)
    with pytest.raises(TypeError):
        recognition_flow.capture_frame(ctrl, record_screenshot=None)
