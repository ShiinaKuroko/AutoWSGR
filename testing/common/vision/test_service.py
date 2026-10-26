"""模块功能：验证 common.vision 的公共入口和通用组合流程。

直接调用方：项目测试运行器。

直接依赖：NumPy、pytest 和 common.vision 公共能力。

边界：不初始化真实设备，不加载 MaaFramework OCR 模型，不验证上层业务识别规则。
"""

from __future__ import annotations

import numpy as np
import pytest

from autowsgr.common import vision
from autowsgr.common.vision import service
from autowsgr.common.vision.adapters import match_pixels, match_template, text_recognition
from autowsgr.common.vision.adapters.pixel_matching import Color, PixelRule, PixelSignature
from autowsgr.common.vision.adapters.template_matching import ROI, Template
from autowsgr.common.vision.ocr import TextDetection


def test_public_service_exports_are_stable() -> None:
    """公共入口只暴露识别功能与识别数据模型。"""
    entries = (
        'screenshot',
        'expect_template',
        'expect_ocr',
        'expect_pixels',
        'expect_template_center',
        'expect_ocr_center',
        'expect_pixel_center',
    )
    for entry in entries:
        assert callable(getattr(vision, entry))
    assert vision.ROI is ROI
    assert vision.Template is Template
    assert vision.RecognitionResult is service.RecognitionResult


def test_pixel_matching_composes_roi_sampling_and_rule_evaluation() -> None:
    """像素匹配可以在 ROI 内采样并返回规则结果。"""
    image = np.zeros((20, 30, 3), dtype=np.uint8)
    image[10, 15] = (10, 20, 30)
    signature = PixelSignature(
        name='pixel',
        rules=(PixelRule(0.5, 0.5, Color(10, 20, 30)),),
    )

    result = match_pixels(image, signature, roi=ROI(0.0, 0.0, 1.0, 1.0))

    assert result.matched
    assert result.matched_count == 1
    assert result.ratio == 1.0


def test_template_matching_returns_absolute_location_from_roi() -> None:
    """模板匹配应把 ROI 内位置还原为原图像素坐标。"""
    template_image = np.arange(10 * 12 * 3, dtype=np.uint8).reshape((10, 12, 3))
    image = np.full((60, 80, 3), 17, dtype=np.uint8)
    image[20:30, 30:42] = template_image
    template = Template(
        name='sample',
        relative_path='sample.png',
        image=template_image,
        source_resolution=(80, 60),
    )

    result = match_template(
        image,
        template,
        roi=ROI(0.25, 0.25, 0.8, 0.9),
        confidence=0.99,
    )

    assert result.matched
    assert result.location == (30, 20)
    assert result.template_path == 'sample.png'


def test_text_preparation_and_counter_parser() -> None:
    """文本预处理保持 RGB 输出，计数解析覆盖分隔符和丢失分隔符。"""
    image = np.zeros((5, 7, 3), dtype=np.uint8)

    prepared = text_recognition.prepare_text(image)

    assert prepared.shape == (20, 28, 3)
    assert text_recognition.parse_counter('3/10', 10) == 3
    assert text_recognition.parse_counter('310', 10) == 3
    with pytest.raises(ValueError, match='文本中无数字'):
        text_recognition.parse_counter('none', 10)


def test_ocr_entry_uses_profile_and_candidate_constraint(monkeypatch: pytest.MonkeyPatch) -> None:
    """OCR 组合方法应选择识别模式并应用候选约束。"""

    class FakeOCRExecutor:
        def recognize_line(
            self,
            image: np.ndarray,
            allowlist: str,
        ) -> list[TextDetection]:
            assert image.shape == (10, 12, 3)
            assert allowlist == '0123456789'
            return [TextDetection('123', 0.95, (0, 0, 12, 10))]

        def recognize(
            self,
            _image: np.ndarray,
            _allowlist: str,
        ) -> list[TextDetection]:
            raise AssertionError('单行识别配置不应调用完整识别入口')

    monkeypatch.setattr(text_recognition, '_ocr_executor', FakeOCRExecutor)

    result = text_recognition.recognize_text(
        np.zeros((10, 12, 3), dtype=np.uint8),
        allowlist='0123456789',
        recognition_profile='single_line',
        candidates=('123',),
    )

    assert result == [TextDetection('123', 0.95, (0, 0, 12, 10))]


def test_ocr_expect_accepts_candidate_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    """OCR 期望支持候选集合：命中任一即算找到。"""
    detections = [TextDetection('最强之舟（困难）', 0.91, (0, 0, 20, 10))]
    monkeypatch.setattr(service.adapters, 'recognize_text', lambda *_args, **_kwargs: detections)
    monkeypatch.setattr(
        service,
        '_retry',
        lambda _ctx, *, observe, accept, **_kwargs: service.RecognitionResult(
            accept(observe(None)), detections, None
        ),
    )

    assert service.expect_ocr(object(), expect='最强之舟（困难）').satisfied is True
    assert service.expect_ocr(object(), expect=('最强之舟', '最强之舟（困难）')).satisfied is True
    assert service.expect_ocr(object(), expect=('最强之舟',)).satisfied is False


def test_ocr_expect_rejects_empty_candidate_collection() -> None:
    """空候选集合属于非法期望，必须显式失败。"""
    with pytest.raises(ValueError, match='候选集合不能为空'):
        service.expect_ocr(object(), expect=())
