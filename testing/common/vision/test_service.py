"""模块功能：验证 common.vision 的公共入口和通用组合流程。

直接调用方：项目测试运行器。

直接依赖：NumPy、pytest 和 common.vision 公共能力。

边界：不初始化真实设备，不加载 MaaFramework OCR 模型，不验证上层业务识别规则。
"""

from __future__ import annotations

import numpy as np
import pytest

from autowsgr.common import vision
from autowsgr.common.vision.numpy_engine import NumpyExecutor
from autowsgr.common.vision.ocr_engine import TextDetection
from autowsgr.common.vision.opencv_engine import OpenCVExecutor
from autowsgr.common.vision.operations import text_recognition
from autowsgr.common.vision.operations.pixel_matching import Color, PixelRule, PixelSignature
from autowsgr.common.vision.operations.template_matching import ROI, Template


def test_public_service_exports_are_stable() -> None:
    """公共入口暴露三种基础能力和组合操作。"""
    assert isinstance(vision.numpy, NumpyExecutor)
    assert isinstance(vision.opencv, OpenCVExecutor)
    assert vision.ocr is text_recognition.recognize_text
    assert vision.match_pixels is not None
    assert vision.match_template is not None


def test_pixel_matching_composes_roi_sampling_and_rule_evaluation() -> None:
    """像素匹配可以在 ROI 内采样并返回规则结果。"""
    image = np.zeros((20, 30, 3), dtype=np.uint8)
    image[10, 15] = (10, 20, 30)
    signature = PixelSignature(
        name='pixel',
        rules=(PixelRule(0.5, 0.5, Color(10, 20, 30)),),
    )

    result = vision.match_pixels(image, signature, roi=ROI(0.0, 0.0, 1.0, 1.0))

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

    result = vision.match_template(
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

    prepared = vision.prepare_text(image)

    assert prepared.shape == (20, 28, 3)
    assert vision.parse_counter('3/10', 10) == 3
    assert vision.parse_counter('310', 10) == 3
    with pytest.raises(ValueError, match='文本中无数字'):
        vision.parse_counter('none', 10)


def test_ocr_entry_uses_profile_and_candidate_constraint(monkeypatch: pytest.MonkeyPatch) -> None:
    """OCR 公共入口应选择识别模式并应用候选约束。"""

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

    result = vision.ocr(
        np.zeros((10, 12, 3), dtype=np.uint8),
        allowlist='0123456789',
        recognition_profile='single_line',
        candidates=('123',),
    )

    assert result == [TextDetection('123', 0.95, (0, 0, 12, 10))]
