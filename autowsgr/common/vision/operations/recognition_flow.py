"""模块功能：提供 common.vision 的唯一公共入口，完成截图、前识别和后识别。

上层调用：
- application、business、dispatch 和 server：确认当前状态或操作结果。
- 调用方只提供识别数据和识别规则，不直接调用底层视觉算法。

下层依赖：
- operations 的模板匹配、OCR 和像素匹配组合能力。
- dispatch.context.ContextHandle：提供设备服务和截图事实写入（仅类型注解使用）。

本模块只编排「截图 → 识别 → 比对预期 → 重试」，不决定识别什么、不执行点击、
不解析页面语义；识别数据、识别规则和预期全部由调用方提供。
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from autowsgr.common.vision.config import OPENCV_TEMPLATE_CONFIDENCE
from autowsgr.common.vision.operations.pixel_matching import match_pixels
from autowsgr.common.vision.operations.template_matching import (
    ROI,
    Template,
    match_template,
)
from autowsgr.common.vision.operations.text_recognition import recognize_text


if TYPE_CHECKING:
    import numpy

    from autowsgr.common.vision.ocr_engine.executor import TextDetection
    from autowsgr.common.vision.operations.pixel_matching import (
        CompositePixelSignature,
        PixelMatchResult,
        PixelSignature,
    )
    from autowsgr.common.vision.operations.template_matching import TemplateMatchResult
    from autowsgr.dispatch.context import ContextHandle


# 识别流程的重试参数：每次失败都重新截图再试。
DEFAULT_RECOGNITION_ATTEMPTS = 3
DEFAULT_RECOGNITION_INTERVAL_SECONDS = 0.5


@dataclass(frozen=True, slots=True)
class RecognitionResult[T]:
    """一次识别流程的结果。

    属性：
        ok: 前识别是否符合预期；后识别是否确认目标已经消失。
        value: 最后一次识别的实际结果。
        frame: 最后一次识别使用的截图。
    """

    ok: bool
    value: T
    frame: numpy.ndarray


# -- 截图 ----------------------------------------------------------------------


def shot(ctx: ContextHandle) -> numpy.ndarray:
    """截取当前画面并把这一帧写入任务上下文。

    参数：
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。

    返回：
        当前设备截图。
    """
    frame = ctx.runtime.ctrl.screenshot()
    ctx.record_screenshot(frame)
    return frame


# -- 前识别 --------------------------------------------------------------------


def before_template(
    ctx: ContextHandle,
    *,
    template: Template | Sequence[Template],
    roi: ROI | Sequence[ROI | None] | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
    min_matches: int = 1,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
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
        ok 表示命中数量是否达到预期。
    """
    required = _required_matches(template, min_matches)
    return _repeat(
        ctx,
        observe=lambda frame: _match_templates(frame, template, roi, confidence),
        accept=lambda value: _matched_count(value) >= required,
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
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[list[TextDetection]]:
    """前识别：重试 OCR，直到实际文本与调用方期望结果一致。

    OCR 实际文本与 expect 做直接相等比对；模糊匹配、去噪和纠错属于调用方的
    后处理规则，不在本模块内实现。

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
        ok 表示本次实际结果中是否存在与期望一致的文本。
    """
    return _repeat(
        ctx,
        observe=lambda frame: recognize_text(
            frame,
            roi=roi,
            allowlist=allowlist,
            recognition_profile=recognition_profile,
            candidates=candidates,
        ),
        accept=lambda value: _text_found(value, expect),
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def before_pixels(
    ctx: ContextHandle,
    *,
    signature: PixelSignature | CompositePixelSignature,
    roi: ROI | None = None,
    with_details: bool = False,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
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
        ok 表示像素规则是否命中。
    """
    return _repeat(
        ctx,
        observe=lambda frame: match_pixels(
            frame,
            signature,
            roi=roi,
            with_details=with_details,
        ),
        accept=lambda value: bool(value.matched),
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


# -- 后识别 --------------------------------------------------------------------


def after_template(
    ctx: ContextHandle,
    *,
    template: Template | Sequence[Template],
    roi: ROI | Sequence[ROI | None] | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
    min_matches: int = 1,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[TemplateMatchResult | tuple[TemplateMatchResult, ...]]:
    """后识别：重试模板匹配，直到命中数量低于预期，确认目标已经消失。

    参数与 before_template 相同，判定方向相反。
    """
    required = _required_matches(template, min_matches)
    return _repeat(
        ctx,
        observe=lambda frame: _match_templates(frame, template, roi, confidence),
        accept=lambda value: _matched_count(value) < required,
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
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[list[TextDetection]]:
    """后识别：重试 OCR，直到期望文本不再出现，确认操作已经生效。

    参数与 before_ocr 相同，判定方向相反；文本比对规则仍为直接相等。
    """
    return _repeat(
        ctx,
        observe=lambda frame: recognize_text(
            frame,
            roi=roi,
            allowlist=allowlist,
            recognition_profile=recognition_profile,
            candidates=candidates,
        ),
        accept=lambda value: not _text_found(value, expect),
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def after_pixels(
    ctx: ContextHandle,
    *,
    signature: PixelSignature | CompositePixelSignature,
    roi: ROI | None = None,
    with_details: bool = False,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[PixelMatchResult]:
    """后识别：重试像素匹配，直到签名不再命中，确认操作已经生效。

    参数与 before_pixels 相同，判定方向相反。
    """
    return _repeat(
        ctx,
        observe=lambda frame: match_pixels(
            frame,
            signature,
            roi=roi,
            with_details=with_details,
        ),
        accept=lambda value: not value.matched,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


# -- 公共循环 ------------------------------------------------------------------


def _repeat[T](
    ctx: ContextHandle,
    *,
    observe: Callable[[numpy.ndarray], T],
    accept: Callable[[T], bool],
    attempts: int,
    interval_seconds: float,
) -> RecognitionResult[T]:
    """重试「截图 → 识别 → 比对预期」，直到符合预期或用完次数。"""
    _validate_retry_options(attempts, interval_seconds)
    value: T | None = None
    frame: numpy.ndarray | None = None
    for attempt in range(1, attempts + 1):
        frame = shot(ctx)
        value = observe(frame)
        if accept(value):
            return RecognitionResult(True, value, frame)
        if attempt < attempts:
            time.sleep(interval_seconds)
    if value is None or frame is None:
        raise ValueError('attempts 必须大于零')
    return RecognitionResult(False, value, frame)


# -- 识别规则 ------------------------------------------------------------------


def _match_templates(
    frame: numpy.ndarray,
    template: Template | Sequence[Template],
    roi: ROI | Sequence[ROI | None] | None,
    confidence: float,
) -> TemplateMatchResult | tuple[TemplateMatchResult, ...]:
    """按单模板或多模板顺序执行模板匹配。"""
    if not 0.0 <= confidence <= 1.0:
        raise ValueError('confidence 必须位于 0 到 1 之间')
    inputs, single = _template_inputs(template, roi)
    results = tuple(
        match_template(frame, item, roi=item_roi, confidence=confidence)
        for item, item_roi in inputs
    )
    return results[0] if single else results


def _template_inputs(
    template: Template | Sequence[Template],
    roi: ROI | Sequence[ROI | None] | None,
) -> tuple[tuple[tuple[Template, ROI | None], ...], bool]:
    """规范化单模板或按顺序排列的模板与区域。"""
    if isinstance(template, Template):
        if isinstance(roi, Sequence) and not isinstance(roi, (str, bytes)):
            raise TypeError('单模板的 roi 必须是 ROI 或 None')
        if roi is not None and not isinstance(roi, ROI):
            raise TypeError('roi 必须是 ROI 或 None')
        return ((template, roi),), True

    if isinstance(template, (str, bytes)) or not isinstance(template, Sequence):
        raise TypeError('template 必须是 Template 或 Template 序列')
    templates = tuple(template)
    if not templates:
        raise ValueError('template 序列不能为空')
    if not all(isinstance(item, Template) for item in templates):
        raise TypeError('template 序列中的元素必须是 Template')

    if roi is None or isinstance(roi, ROI):
        rois = (roi,) * len(templates)
    elif isinstance(roi, Sequence) and not isinstance(roi, (str, bytes)):
        rois = tuple(roi)
        if len(rois) != len(templates):
            raise ValueError('roi 序列长度必须与 template 序列一致')
        if not all(item is None or isinstance(item, ROI) for item in rois):
            raise TypeError('roi 序列中的元素必须是 ROI 或 None')
    else:
        raise TypeError('roi 必须是 ROI、ROI 序列或 None')

    return tuple(zip(templates, rois, strict=True)), False


def _matched_count(value: TemplateMatchResult | tuple[TemplateMatchResult, ...]) -> int:
    """统计实际命中的模板数量。"""
    if isinstance(value, tuple):
        return sum(1 for item in value if item.matched)
    return 1 if value.matched else 0


def _text_found(value: list[TextDetection], expect: str) -> bool:
    """判断 OCR 实际文本中是否存在与期望完全一致的条目。"""
    return any(detection.recognized_text == expect for detection in value)


def _required_matches(
    template: Template | Sequence[Template],
    min_matches: int,
) -> int:
    """校验并返回调用方期望的命中数量。"""
    if isinstance(min_matches, bool) or not isinstance(min_matches, int):
        raise TypeError('min_matches 必须是整数')
    if isinstance(template, Template):
        if min_matches != 1:
            raise ValueError('单模板匹配的 min_matches 只能是 1')
        return 1
    inputs, _ = _template_inputs(template, None)
    if not 1 <= min_matches <= len(inputs):
        raise ValueError(f'min_matches 必须位于 1 到 {len(inputs)} 之间')
    return min_matches


def _validate_retry_options(attempts: int, interval_seconds: float) -> None:
    """校验重试次数和等待间隔。"""
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        raise ValueError('attempts 必须是大于零的整数')
    if isinstance(interval_seconds, bool) or interval_seconds < 0:
        raise ValueError('interval_seconds 不能小于零')


__all__ = [
    'DEFAULT_RECOGNITION_ATTEMPTS',
    'DEFAULT_RECOGNITION_INTERVAL_SECONDS',
    'RecognitionResult',
    'after_ocr',
    'after_pixels',
    'after_template',
    'before_ocr',
    'before_pixels',
    'before_template',
    'shot',
]
