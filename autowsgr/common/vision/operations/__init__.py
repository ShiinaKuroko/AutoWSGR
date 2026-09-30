"""模块功能：聚合 NumPy、OpenCV 和 FastOCR 的通用组合操作。

直接调用方：service 入口及需要复用完整视觉流程的通用模块。

直接依赖：pixel_matching、template_matching 和 text_recognition。

边界：不持有设备截图、页面状态或业务领域识别规则。
"""

from __future__ import annotations

from autowsgr.common.vision.operations.pixel_matching import match_pixels
from autowsgr.common.vision.operations.template_matching import (
    match_template,
    match_templates,
)
from autowsgr.common.vision.operations.text_recognition import (
    parse_counter,
    prepare_text,
    recognize_prepared_text,
    recognize_text,
)


__all__ = [
    'match_pixels',
    'match_template',
    'match_templates',
    'parse_counter',
    'prepare_text',
    'recognize_prepared_text',
    'recognize_text',
]
