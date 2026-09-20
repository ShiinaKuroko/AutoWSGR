"""模块功能：聚合通用视觉能力并提供 service 级入口。

直接调用方：common.vision 公共门面及需要明确 service 边界的上层模块。

直接依赖：NumPy、OpenCV 和 OCR 执行器，以及 operations 中的完整视觉流程。

边界：不持有设备截图、页面状态、业务识别规则或调度上下文。
"""

from __future__ import annotations

from autowsgr.common.vision.numpy_engine import NumpyExecutor
from autowsgr.common.vision.opencv_engine import OpenCVExecutor
from autowsgr.common.vision.operations import (
    match_pixels,
    match_template,
    match_templates,
    parse_counter,
    prepare_text,
    recognize_prepared_text,
    recognize_text,
)


# ── 基础执行入口 ───────────────────────────────────────────────────

numpy = NumpyExecutor()
opencv = OpenCVExecutor()


# ── 组合能力入口 ───────────────────────────────────────────────────

ocr = recognize_text


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
