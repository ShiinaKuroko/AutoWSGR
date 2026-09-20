"""模块功能：提供通用视觉能力的稳定入口。

直接调用方：application、business 和 tools 中需要视觉处理的模块。

直接依赖：service 入口及其下层视觉操作和基础执行器。

边界：不承载视觉算法实现、业务识别规则、设备截图或页面流程。
"""

from __future__ import annotations

from autowsgr.common.vision.service import (
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
)


__all__ = [
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
]
