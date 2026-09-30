"""模块功能：聚合通用视觉能力并提供 service 级公共入口。

直接调用方：common.vision 公共门面及需要明确 service 边界的上层模块。

直接依赖：operations 的通用视觉流程，以及 NumPy、OpenCV 和 OCR 执行器。

边界：service 只定义公开入口和数据转发，不实现视觉算法、不决定识别规则；取图和重试的
执行细节由 operations.recognition_flow 承担。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common.vision.config import OPENCV_TEMPLATE_CONFIDENCE
from autowsgr.common.vision.numpy_engine import NumpyExecutor
from autowsgr.common.vision.opencv_engine import OpenCVExecutor
from autowsgr.common.vision.operations import (
    match_pixels,
    match_template,
    match_templates,
    parse_counter,
    prepare_text,
    recognition_flow,
    recognize_prepared_text,
    recognize_text,
)


if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np

    from autowsgr.common.vision.ocr_engine.executor import TextDetection
    from autowsgr.common.vision.operations.pixel_matching import (
        CompositePixelSignature,
        PixelMatchResult,
        PixelSignature,
    )
    from autowsgr.common.vision.operations.template_matching import (
        ROI,
        Template,
        TemplateMatchResult,
    )
    from autowsgr.dispatch.context import ContextHandle


# ── 基础执行入口 ───────────────────────────────────────────────────

numpy = NumpyExecutor()
opencv = OpenCVExecutor()


# ── 组合能力入口 ───────────────────────────────────────────────────

ocr = recognize_text

RecognitionResult = recognition_flow.RecognitionResult


# ── 公共识别入口 ───────────────────────────────────────────────────


def shot(ctx: ContextHandle) -> np.ndarray:
    """截取当前画面并把这一帧写入任务上下文。

    参数：
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。

    返回：
        当前设备截图。
    """
    return recognition_flow.capture(ctx)


def before_template(
    ctx: ContextHandle,
    *,
    template: Template | Sequence[Template],
    roi: ROI | Sequence[ROI | None] | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
    min_matches: int = 1,
    attempts: int = recognition_flow.DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = recognition_flow.DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[TemplateMatchResult | tuple[TemplateMatchResult, ...]]:
    """前识别：重试模板匹配，直到命中数量达到调用方预期。

    参数：
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        template: 单个模板，或需要逐个匹配的一组模板。
        roi: 搜索区域；多模板时可为共享区域或逐模板区域。
        confidence: 期望的匹配置信度，模板分数达到它才算命中。
        min_matches: 期望命中的模板数量；单模板只能为 1。
        attempts: 最大识别次数。
        interval_seconds: 两次识别之间的等待秒数。

    返回：
        ok 表示命中数量是否达到预期，value 是最后一次匹配的实际结果。
    """
    return recognition_flow.run_template(
        ctx,
        template=template,
        roi=roi,
        confidence=confidence,
        min_matches=min_matches,
        expect_present=True,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def after_template(
    ctx: ContextHandle,
    *,
    template: Template | Sequence[Template],
    roi: ROI | Sequence[ROI | None] | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
    min_matches: int = 1,
    attempts: int = recognition_flow.DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = recognition_flow.DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[TemplateMatchResult | tuple[TemplateMatchResult, ...]]:
    """后识别：重试模板匹配，直到命中数量低于预期，确认目标已经消失。

    参数与 before_template 相同，判定方向相反；ok 表示是否确认目标已经消失。
    """
    return recognition_flow.run_template(
        ctx,
        template=template,
        roi=roi,
        confidence=confidence,
        min_matches=min_matches,
        expect_present=False,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def before_ocr(
    ctx: ContextHandle,
    *,
    expect: str,
    roi: ROI | None = None,
    allowlist: str = '',
    recognition_profile: str = 'full',
    candidates: Sequence[str] | None = None,
    attempts: int = recognition_flow.DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = recognition_flow.DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[list[TextDetection]]:
    """前识别：重试 OCR，直到实际文本与调用方期望结果一致。

    OCR 实际文本与 expect 直接相等比对；模糊匹配、去噪和纠错属于调用方的后处理规则，
    不在视觉层实现。

    参数：
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        expect: 调用方期望识别到的完整文本。
        roi: OCR 搜索区域。
        allowlist: 允许识别的字符集合。
        recognition_profile: OCR 识别配置名称。
        candidates: OCR 完整文本候选集合。
        attempts: 最大识别次数。
        interval_seconds: 两次识别之间的等待秒数。

    返回：
        ok 表示是否识别到期望文本，value 是最后一次 OCR 的实际结果。
    """
    return recognition_flow.run_ocr(
        ctx,
        expect=expect,
        expect_present=True,
        roi=roi,
        allowlist=allowlist,
        recognition_profile=recognition_profile,
        candidates=candidates,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def after_ocr(
    ctx: ContextHandle,
    *,
    expect: str,
    roi: ROI | None = None,
    allowlist: str = '',
    recognition_profile: str = 'full',
    candidates: Sequence[str] | None = None,
    attempts: int = recognition_flow.DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = recognition_flow.DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[list[TextDetection]]:
    """后识别：重试 OCR，直到期望文本不再出现，确认操作已经生效。

    参数与 before_ocr 相同，判定方向相反；ok 表示期望文本是否已经消失。
    """
    return recognition_flow.run_ocr(
        ctx,
        expect=expect,
        expect_present=False,
        roi=roi,
        allowlist=allowlist,
        recognition_profile=recognition_profile,
        candidates=candidates,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def before_pixels(
    ctx: ContextHandle,
    *,
    signature: PixelSignature | CompositePixelSignature,
    roi: ROI | None = None,
    with_details: bool = False,
    attempts: int = recognition_flow.DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = recognition_flow.DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[PixelMatchResult]:
    """前识别：重试像素匹配，直到调用方给的签名判定命中。

    参数：
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        signature: 调用方定义的像素规则或规则组合。
        roi: 采样区域。
        with_details: 是否要求结果包含逐规则详情。
        attempts: 最大识别次数。
        interval_seconds: 两次识别之间的等待秒数。

    返回：
        ok 表示像素规则是否命中，value 是最后一次匹配的实际结果。
    """
    return recognition_flow.run_pixels(
        ctx,
        signature=signature,
        expect_present=True,
        roi=roi,
        with_details=with_details,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def after_pixels(
    ctx: ContextHandle,
    *,
    signature: PixelSignature | CompositePixelSignature,
    roi: ROI | None = None,
    with_details: bool = False,
    attempts: int = recognition_flow.DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = recognition_flow.DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[PixelMatchResult]:
    """后识别：重试像素匹配，直到签名不再命中，确认操作已经生效。

    参数与 before_pixels 相同，判定方向相反；ok 表示签名是否已经不再命中。
    """
    return recognition_flow.run_pixels(
        ctx,
        signature=signature,
        expect_present=False,
        roi=roi,
        with_details=with_details,
        attempts=attempts,
        interval_seconds=interval_seconds,
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
