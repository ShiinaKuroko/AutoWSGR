"""模块功能：聚合通用视觉能力并提供 service 级入口。

直接调用方：common.vision 公共门面及需要明确 service 边界的上层模块。

直接依赖：NumPy、OpenCV 和 OCR 执行器，以及 operations 中的完整视觉流程。

边界：只聚合视觉能力出口；截图和重试编排由 operations.recognition_flow 通过调用方传入的 ContextHandle 完成。
"""

from __future__ import annotations

from autowsgr.common.vision.numpy_engine import NumpyExecutor
from autowsgr.common.vision.opencv_engine import OpenCVExecutor
from autowsgr.common.vision.operations import (
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
    parse_counter,
    prepare_text,
    recognize_prepared_text,
    recognize_text,
    shot,
)


# ── 基础执行入口 ───────────────────────────────────────────────────

numpy = NumpyExecutor()
opencv = OpenCVExecutor()


# ── 组合能力入口 ───────────────────────────────────────────────────

ocr = recognize_text


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
