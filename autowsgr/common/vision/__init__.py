"""模块功能：提供通用视觉能力的稳定入口。

直接调用方：application、business 和 tools 中需要视觉处理的模块。

直接依赖：service 入口及其下层视觉操作和基础执行器。

边界：只导出稳定视觉入口和识别结果模型；识别数据、识别规则和预期由调用方提供，不实现业务识别规则或页面流程。
"""

from __future__ import annotations

from autowsgr.common.vision.service import (
    RecognitionResult,
    after_ocr,
    after_pixels,
    after_template,
    before_ocr,
    before_pixels,
    before_template,
    match_pixels,
    match_template,
    match_templates,
    numpy,
    ocr,
    opencv,
    parse_counter,
    prepare_text,
    recognize_prepared_text,
    recognize_text,
    shot,
)


__all__ = [
    'RecognitionResult',
    'after_ocr',
    'after_pixels',
    'after_template',
    'before_ocr',
    'before_pixels',
    'before_template',
    'match_pixels',
    'match_template',
    'match_templates',
    'numpy',
    'ocr',
    'opencv',
    'parse_counter',
    'prepare_text',
    'recognize_prepared_text',
    'recognize_text',
    'shot',
]
