"""模块功能：提供 common.vision 的八个公共识别能力。

上层调用：
- application、business、dispatch 和 server：确认当前状态或操作结果。

下层依赖：
- adapters：提供模板匹配、OCR 和像素匹配等重新修饰后的视觉方法。
- dispatch.context：提供设备服务和截图事实写入（仅类型注解使用）。

边界：只提供截图、前识别和后识别八个功能；识别数据、识别规则和预期全部由调用方
提供，service 不决定识别什么、不执行点击、不解析页面语义。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision.adapters import match_pixels, match_templates, recognize_text
from autowsgr.common.vision.config import (
    DEFAULT_RECOGNITION_ATTEMPTS,
    DEFAULT_RECOGNITION_INTERVAL_SECONDS,
    OPENCV_TEMPLATE_CONFIDENCE,
)


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    import numpy

    from autowsgr.common.vision.adapters.pixel_matching import (
        CompositePixelSignature,
        PixelMatchResult,
        PixelSignature,
    )
    from autowsgr.common.vision.adapters.template_matching import (
        ROI,
        Template,
        TemplateMatchResult,
    )
    from autowsgr.common.vision.ocr_engine import TextDetection
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('vision.recognition')


# ── 识别结果 ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class RecognitionResult[T]:
    """一次识别请求的结果。

    Attributes:
        satisfied: 识别结果是否满足调用方给出的预期。
        observation: 本次识别的观测值，类型随识别类型而定。
        screenshot: 做出本次判定所使用的画面。
    """

    satisfied: bool
    observation: T
    screenshot: numpy.ndarray


# ── 公共识别入口 ────────────────────────────────────────────────────────────────────


def shot(ctx: ContextHandle) -> numpy.ndarray:
    """截取当前画面并把这一帧登记为任务上下文的最新截图。

    Args:
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。

    Returns:
        当前设备截图。
    """
    # 先取画面再登记，保证上下文中的最新截图就是本次判定使用的画面。
    frame = ctx.runtime.ctrl.screenshot()
    ctx.record_screenshot(frame)
    return frame


def expect_template(
    ctx: ContextHandle,
    *,
    template: Template | Sequence[Template],
    roi: ROI | Sequence[ROI | None] | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
    min_matches: int = 1,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[list[TemplateMatchResult]]:
    """前识别：重试模板匹配，直到命中数量达到调用方预期。

    Args:
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        template: 单个模板，或需要逐个匹配的一组模板。
        roi: 共享搜索区域，或与模板一一对应的区域序列。
        confidence: 期望的匹配置信度，模板分数达到它才算命中。
        min_matches: 期望命中的模板数量。
        attempts: 最大识别次数。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        satisfied 表示命中数量是否达到预期；observation 是最后一次匹配结果列表。
    """
    required = _required_matches(min_matches)
    return _retry(
        ctx,
        task='模板识别',
        observe=lambda frame: match_templates(frame, template, roi=roi, confidence=confidence),
        accept=lambda matches: _matched_count(matches) >= required,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def expect_template_center(
    ctx: ContextHandle,
    *,
    template: Template | Sequence[Template],
    roi: ROI | Sequence[ROI | None] | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> tuple[float, float] | None:
    """前识别：重试模板匹配并返回第一个命中模板的中心。

    Args:
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        template: 单个模板，或需要逐个匹配的一组模板。
        roi: 共享搜索区域，或与模板一一对应的区域序列。
        confidence: 期望的匹配置信度，模板分数达到它才算命中。
        attempts: 最大识别次数。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        第一个命中模板的归一化中心；没有命中时为 None。
    """
    result = expect_template(
        ctx,
        template=template,
        roi=roi,
        confidence=confidence,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )
    for match in result.observation:
        if match.matched and match.center is not None:
            return match.center
    return None


def expect_ocr(
    ctx: ContextHandle,
    *,
    expect: str | Sequence[str],
    roi: ROI | None = None,
    allowlist: str = '',
    recognition_profile: str = 'full',
    candidates: Sequence[str] | None = None,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[list[TextDetection]]:
    """前识别：重试 OCR，直到实际文本与调用方期望结果一致。

    OCR 实际文本与 expect 直接相等比对；模糊匹配、去噪和纠错属于调用方的后处理规则。

    Args:
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        expect: 期望识别到的完整文本，或候选集合；候选集合命中任一即算符合预期。
        roi: OCR 识别区域。
        allowlist: 允许识别的字符集合。
        recognition_profile: OCR 识别配置名称。
        candidates: OCR 完整文本候选集合。
        attempts: 最大识别次数。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        satisfied 表示是否识别到期望文本；observation 是最后一次 OCR 结果。
    """
    return _retry(
        ctx,
        task='OCR 识别',
        observe=lambda frame: recognize_text(
            frame,
            roi=roi,
            allowlist=allowlist,
            recognition_profile=recognition_profile,
            candidates=candidates,
        ),
        accept=lambda detections: _text_found(detections, expect),
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def expect_pixels(
    ctx: ContextHandle,
    *,
    signature: PixelSignature | CompositePixelSignature,
    roi: ROI | None = None,
    with_details: bool = False,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[PixelMatchResult]:
    """前识别：重试像素匹配，直到调用方给的签名判定命中。

    Args:
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        signature: 调用方定义的像素规则或规则组合。
        roi: 采样区域。
        with_details: 是否要求结果包含逐规则详情。
        attempts: 最大识别次数。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        satisfied 表示签名是否命中；observation 是最后一次像素匹配结果。
    """
    return _retry(
        ctx,
        task='像素识别',
        observe=lambda frame: match_pixels(
            frame,
            signature,
            roi=roi,
            with_details=with_details,
        ),
        accept=lambda result: result.matched,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def expect_template_absent(
    ctx: ContextHandle,
    *,
    template: Template | Sequence[Template],
    roi: ROI | Sequence[ROI | None] | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
    min_matches: int = 1,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[list[TemplateMatchResult]]:
    """后识别：重试模板匹配，直到命中数量低于预期，确认目标已经消失。

    Args:
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        template: 单个模板，或需要逐个匹配的一组模板。
        roi: 共享搜索区域，或与模板一一对应的区域序列。
        confidence: 期望的匹配置信度，模板分数达到它才算命中。
        min_matches: 期望命中的模板数量。
        attempts: 最大确认次数。
        interval_seconds: 两次确认之间的等待秒数。

    Returns:
        satisfied 表示是否确认目标已经消失；observation 是最后一次匹配结果列表。
    """
    required = _required_matches(min_matches)
    # 后识别确认目标消失，因此命中数量低于预期才算符合预期。
    return _retry(
        ctx,
        task='模板识别',
        observe=lambda frame: match_templates(frame, template, roi=roi, confidence=confidence),
        accept=lambda matches: _matched_count(matches) < required,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def expect_ocr_absent(
    ctx: ContextHandle,
    *,
    expect: str | Sequence[str],
    roi: ROI | None = None,
    allowlist: str = '',
    recognition_profile: str = 'full',
    candidates: Sequence[str] | None = None,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[list[TextDetection]]:
    """后识别：重试 OCR，直到期望文本不再出现，确认操作已经生效。

    Args:
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        expect: 期望已经消失的完整文本，或候选集合；候选集合全部不出现才算符合预期。
        roi: OCR 识别区域。
        allowlist: 允许识别的字符集合。
        recognition_profile: OCR 识别配置名称。
        candidates: OCR 完整文本候选集合。
        attempts: 最大确认次数。
        interval_seconds: 两次确认之间的等待秒数。

    Returns:
        satisfied 表示期望文本是否已经消失；observation 是最后一次 OCR 结果。
    """
    # 后识别确认文本消失，因此期望文本不再出现才算符合预期。
    return _retry(
        ctx,
        task='OCR 识别',
        observe=lambda frame: recognize_text(
            frame,
            roi=roi,
            allowlist=allowlist,
            recognition_profile=recognition_profile,
            candidates=candidates,
        ),
        accept=lambda detections: not _text_found(detections, expect),
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def expect_pixels_absent(
    ctx: ContextHandle,
    *,
    signature: PixelSignature | CompositePixelSignature,
    roi: ROI | None = None,
    with_details: bool = False,
    attempts: int = DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[PixelMatchResult]:
    """后识别：重试像素匹配，直到签名不再命中，确认操作已经生效。

    Args:
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        signature: 调用方定义的像素规则或规则组合。
        roi: 采样区域。
        with_details: 是否要求结果包含逐规则详情。
        attempts: 最大确认次数。
        interval_seconds: 两次确认之间的等待秒数。

    Returns:
        satisfied 表示签名是否已经不再命中；observation 是最后一次像素匹配结果。
    """
    # 后识别确认状态变化，因此签名不再命中才算符合预期。
    return _retry(
        ctx,
        task='像素识别',
        observe=lambda frame: match_pixels(
            frame,
            signature,
            roi=roi,
            with_details=with_details,
        ),
        accept=lambda result: not result.matched,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


# ── 识别重试和判定 ───────────────────────────────────────────────────────────────────


def _retry[T](
    ctx: ContextHandle,
    *,
    task: str,
    observe: Callable[[numpy.ndarray], T],
    accept: Callable[[T], bool],
    attempts: int,
    interval_seconds: float,
) -> RecognitionResult[T]:
    """按调用方预期重试「截图 → 识别 → 判定预期」。

    Args:
        ctx: 提供设备服务和截图事实写入的统一 ContextHandle。
        task: 日志中标识本次识别任务的业务名称。
        observe: 用一帧画面执行一次识别。
        accept: 判断识别结果是否满足调用方给出的预期。
        attempts: 最大识别次数。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        最近一次识别的结果；satisfied 表示是否满足预期。
    """
    _validate_retry_options(attempts, interval_seconds)
    for attempt in range(1, attempts + 1):
        # 1. 取当前画面并在识别前登记，保证记录与判定使用同一帧。
        screenshot = shot(ctx)
        # 2. 按调用方预期判定本次识别，满足即返回。
        observation = observe(screenshot)
        if accept(observation):
            _log.debug(
                '[VISION] 识别流程 → 确认结果：task={!r}，attempt={}，result={!r}',
                task,
                attempt,
                'satisfied',
            )
            return RecognitionResult(True, observation, screenshot)
        # 3. 未满足且仍有剩余次数时等待后重试，最终结果交给调用方处理。
        if attempt < attempts:
            _log.debug(
                '[VISION] 识别流程 → 重试：task={!r}，attempt={}，max_attempts={}，reason={!r}',
                task,
                attempt,
                attempts,
                'expectation_not_met',
            )
            time.sleep(interval_seconds)
    _log.debug(
        '[VISION] 识别流程 → 确认结果：task={!r}，attempt={}，max_attempts={}，result={!r}',
        task,
        attempts,
        attempts,
        'not_satisfied',
    )
    return RecognitionResult(False, observation, screenshot)


def _matched_count(matches: list[TemplateMatchResult]) -> int:
    """统计模板匹配结果中的命中数量。"""
    return sum(1 for match in matches if match.matched)


def _expected_texts(expect: str | Sequence[str]) -> tuple[str, ...]:
    """把期望文本归一化为非空候选元组。"""
    if isinstance(expect, str):
        return (expect,)
    candidates = tuple(expect)
    if not candidates:
        raise ValueError('expect 候选集合不能为空')
    return candidates


def _text_found(detections: list[TextDetection], expect: str | Sequence[str]) -> bool:
    """判断 OCR 结果中是否存在与任一期望候选完全一致的文本。"""
    expected = _expected_texts(expect)
    return any(detection.recognized_text in expected for detection in detections)


def _required_matches(min_matches: int) -> int:
    """校验调用方给出的期望命中数量。"""
    if isinstance(min_matches, bool) or not isinstance(min_matches, int) or min_matches < 1:
        raise ValueError('min_matches 必须是大于零的整数')
    return min_matches


def _validate_retry_options(attempts: int, interval_seconds: float) -> None:
    """校验重试次数和等待间隔。"""
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        raise ValueError('attempts 必须是大于零的整数')
    if isinstance(interval_seconds, bool) or interval_seconds < 0:
        raise ValueError('interval_seconds 不能小于零')


__all__ = [
    'RecognitionResult',
    'expect_ocr',
    'expect_ocr_absent',
    'expect_pixels',
    'expect_pixels_absent',
    'expect_template',
    'expect_template_absent',
    'expect_template_center',
    'shot',
]
