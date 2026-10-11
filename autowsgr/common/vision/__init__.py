"""模块功能：提供通用视觉能力的稳定入口。

上层调用：
- application、business、dispatch 和 server：取用识别入口和识别数据模型。

下层依赖：
- common.vision.service：提供截图、前识别和后识别的公共入口。
- common.vision.adapters：识别数据模型和匹配结果模型。
- common.vision.ocr_engine：提供 OCR 文本检测结果模型。

边界：只做稳定导出；识别数据、识别规则和预期由调用方提供，不实现业务识别规则或页面流程。
"""

from __future__ import annotations

from autowsgr.common.vision.adapters.pixel_matching import (
    Color,
    CompositePixelSignature,
    MatchStrategy,
    PixelDetail,
    PixelMatchResult,
    PixelRule,
    PixelSignature,
)
from autowsgr.common.vision.adapters.template_matching import (
    ROI,
    Template,
    TemplateMatchResult,
)
from autowsgr.common.vision.adapters.text_recognition import RecognitionProfile
from autowsgr.common.vision.ocr_engine import TextDetection
from autowsgr.common.vision.service import (
    RecognitionResult,
    expect_ocr,
    expect_pixels,
    expect_template,
    expect_template_center,
    shot,
)


__all__ = [
    'ROI',
    'Color',
    'CompositePixelSignature',
    'MatchStrategy',
    'PixelDetail',
    'PixelMatchResult',
    'PixelRule',
    'PixelSignature',
    'RecognitionProfile',
    'RecognitionResult',
    'Template',
    'TemplateMatchResult',
    'TextDetection',
    'expect_ocr',
    'expect_pixels',
    'expect_template',
    'expect_template_center',
    'shot',
]
