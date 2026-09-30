"""提供 UI 模块共享的截图、重试识别和终态确认流程。"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, TypeVar

import numpy

from autowsgr.common import vision
from autowsgr.common.vision.config import OPENCV_TEMPLATE_CONFIDENCE
from autowsgr.common.vision.operations.template_matching import ROI, Template


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.common.device.service import DeviceService
    from autowsgr.common.vision.ocr_engine.executor import TextDetection
    from autowsgr.common.vision.operations.pixel_matching import (
        CompositePixelSignature,
        PixelMatchResult,
        PixelSignature,
    )
    from autowsgr.common.vision.operations.template_matching import TemplateMatchResult


_ResultT = TypeVar('_ResultT')


# -- 公共识别参数 --------------------------------------------------------------

_DEFAULT_RECOGNITION_ATTEMPTS = 3
_DEFAULT_RECOGNITION_INTERVAL_SECONDS = 0.5


class RecognitionMode(StrEnum):
    """公共识别流程支持的视觉识别模式。"""

    OPENCV = 'opencv'
    OCR = 'ocr'
    NUMPY = 'numpy'


@dataclass(frozen=True, slots=True)
class RecognitionResult[T]:
    """保存一次识别流程的最终帧、识别值和终态。"""

    matched: bool
    satisfied: bool
    value: T | None
    frame: numpy.ndarray
    attempts: int


# -- 公共截图流程 --------------------------------------------------------------


def capture_frame(
    ctrl: DeviceService,
    *,
    record_screenshot: Callable[[numpy.ndarray], None],
) -> numpy.ndarray:
    """截图，并按调用方提供的回调写入指定 Context。

    Args:
        ctrl: 提供截图能力的设备控制器。
        record_screenshot: 接收当前截图的 Context 写入回调。

    Returns:
        设备当前截图。
    """
    frame = ctrl.screenshot()
    record_screenshot(frame)
    return frame


# -- 公共正向识别流程 ----------------------------------------------------------


def recognize_with_retry(
    ctrl: DeviceService,
    *,
    mode: RecognitionMode,
    record_screenshot: Callable[[numpy.ndarray], None],
    template: Template | Sequence[Template] | None = None,
    roi: ROI | Sequence[ROI | None] | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
    signature: PixelSignature | CompositePixelSignature | None = None,
    allowlist: str = '',
    recognition_profile: str = 'full',
    candidates: Sequence[str] | None = None,
    with_details: bool = False,
    is_match: Callable[[object], bool] | None = None,
    attempts: int = _DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = _DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[
    TemplateMatchResult | tuple[TemplateMatchResult, ...] | list[TextDetection] | PixelMatchResult
]:
    """截图并重试识别，返回统一的识别结果。

    Args:
        ctrl: 提供截图能力的设备控制器。
        mode: 选择 OpenCV 模板、OCR 或 NumPy 像素识别。
        record_screenshot: 接收每次截图的 Context 写入回调。
        template: OpenCV 模板，或按顺序匹配的一组模板。
        roi: OpenCV 搜索区域；多模板时可为共享区域或逐模板区域。
        confidence: OpenCV 模板匹配阈值。
        signature: NumPy 像素签名。
        allowlist: OCR 允许识别的字符集合。
        recognition_profile: OCR 识别配置名称。
        candidates: OCR 完整文本候选集合。
        with_details: NumPy 结果是否包含逐规则详情。
        is_match: 判断识别结果是否满足当前流程的谓词。
        attempts: 最大识别次数。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        包含最终截图、模式对应识别值、命中状态和实际尝试次数的结果。
    """
    _validate_retry_options(attempts, interval_seconds)
    mode = RecognitionMode(mode)
    _validate_mode_inputs(
        mode=mode,
        template=template,
        roi=roi,
        confidence=confidence,
        signature=signature,
        allowlist=allowlist,
        recognition_profile=recognition_profile,
        candidates=candidates,
        with_details=with_details,
    )
    match_predicate = is_match or _has_value

    # 1. 每次识别前都读取最新截图，并按调用方选择写入 Context。
    for attempt in range(1, attempts + 1):
        frame = capture_frame(ctrl, record_screenshot=record_screenshot)
        # 2. 使用刚写入 Context 的同一帧调用所选视觉能力。
        value = _recognize_frame(
            frame,
            mode=mode,
            template=template,
            roi=roi,
            confidence=confidence,
            signature=signature,
            allowlist=allowlist,
            recognition_profile=recognition_profile,
            candidates=candidates,
            with_details=with_details,
        )
        if match_predicate(value):
            return RecognitionResult(True, True, value, frame, attempt)
        # 3. 未命中时只等待并重试，不在公共层执行点击或抛业务异常。
        if attempt < attempts:
            time.sleep(interval_seconds)

    return RecognitionResult(False, False, value, frame, attempts)


# -- 公共终态确认流程 ----------------------------------------------------------


def wait_until_absent(
    ctrl: DeviceService,
    *,
    mode: RecognitionMode,
    record_screenshot: Callable[[numpy.ndarray], None],
    template: Template | Sequence[Template] | None = None,
    roi: ROI | Sequence[ROI | None] | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
    signature: PixelSignature | CompositePixelSignature | None = None,
    allowlist: str = '',
    recognition_profile: str = 'full',
    candidates: Sequence[str] | None = None,
    with_details: bool = False,
    is_present: Callable[[object], bool] | None = None,
    attempts: int = _DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = _DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[
    TemplateMatchResult | tuple[TemplateMatchResult, ...] | list[TextDetection] | PixelMatchResult
]:
    """截图并重试确认目标消失，不对业务失败抛出页面异常。

    Args:
        ctrl: 提供截图能力的设备控制器。
        mode: 选择 OpenCV 模板、OCR 或 NumPy 像素识别。
        record_screenshot: 接收每次截图的 Context 写入回调。
        template: OpenCV 模板，或按顺序匹配的一组模板。
        roi: OpenCV 搜索区域；多模板时可为共享区域或逐模板区域。
        confidence: OpenCV 模板匹配阈值。
        signature: NumPy 像素签名。
        allowlist: OCR 允许识别的字符集合。
        recognition_profile: OCR 识别配置名称。
        candidates: OCR 完整文本候选集合。
        with_details: NumPy 结果是否包含逐规则详情。
        is_present: 判断识别结果是否仍表示目标存在的谓词。
        attempts: 最大确认次数。
        interval_seconds: 两次确认之间的等待秒数。

    Returns:
        包含最终截图、模式对应识别值、目标存在状态和终态确认结果的结果。
    """
    _validate_retry_options(attempts, interval_seconds)
    mode = RecognitionMode(mode)
    _validate_mode_inputs(
        mode=mode,
        template=template,
        roi=roi,
        confidence=confidence,
        signature=signature,
        allowlist=allowlist,
        recognition_profile=recognition_profile,
        candidates=candidates,
        with_details=with_details,
    )
    presence_predicate = is_present or _has_value

    # 1. 每次确认前都读取最新截图，并按调用方选择写入 Context。
    for attempt in range(1, attempts + 1):
        frame = capture_frame(ctrl, record_screenshot=record_screenshot)
        # 2. 使用刚写入 Context 的同一帧调用所选视觉能力。
        value = _recognize_frame(
            frame,
            mode=mode,
            template=template,
            roi=roi,
            confidence=confidence,
            signature=signature,
            allowlist=allowlist,
            recognition_profile=recognition_profile,
            candidates=candidates,
            with_details=with_details,
        )
        # 3. 目标已消失时立即返回成功，避免无意义的后续操作。
        if not presence_predicate(value):
            return RecognitionResult(False, True, value, frame, attempt)
        # 4. 目标仍存在时只等待并重试，把最终失败交给上层处理。
        if attempt < attempts:
            time.sleep(interval_seconds)

    return RecognitionResult(True, False, value, frame, attempts)


# -- 识别模式分发 --------------------------------------------------------------


def _validate_mode_inputs(
    *,
    mode: RecognitionMode,
    template: Template | Sequence[Template] | None,
    roi: ROI | Sequence[ROI | None] | None,
    confidence: float,
    signature: PixelSignature | CompositePixelSignature | None,
    allowlist: str,
    recognition_profile: str,
    candidates: Sequence[str] | None,
    with_details: bool,
) -> None:
    """在设备截图前校验所选识别模式需要的输入。"""
    if mode is RecognitionMode.OPENCV:
        if (
            template is None
            or signature is not None
            or not 0.0 <= confidence <= 1.0
            or allowlist
            or recognition_profile != 'full'
            or candidates is not None
            or with_details
        ):
            raise ValueError('OpenCV 模式的识别参数无效')
        _template_inputs(template, roi)
        return

    if mode is RecognitionMode.OCR:
        if (
            template is not None
            or signature is not None
            or with_details
            or confidence != OPENCV_TEMPLATE_CONFIDENCE
        ):
            raise ValueError('OCR 模式的识别参数无效')
        if roi is not None and not isinstance(roi, ROI):
            raise TypeError('OCR 模式的 roi 必须是 ROI 或 None')
        return

    if (
        template is not None
        or signature is None
        or allowlist
        or recognition_profile != 'full'
        or candidates is not None
        or confidence != OPENCV_TEMPLATE_CONFIDENCE
    ):
        raise ValueError('NumPy 模式的识别参数无效')
    if roi is not None and not isinstance(roi, ROI):
        raise TypeError('NumPy 模式的 roi 必须是 ROI 或 None')


def _template_inputs(
    template: Template | Sequence[Template],
    roi: ROI | Sequence[ROI | None] | None,
) -> tuple[tuple[tuple[Template, ROI | None], ...], bool]:
    """规范化单模板或按顺序排列的模板和 ROI。"""
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


def _recognize_frame(
    frame: numpy.ndarray,
    *,
    mode: RecognitionMode,
    template: Template | Sequence[Template] | None,
    roi: ROI | Sequence[ROI | None] | None,
    confidence: float,
    signature: PixelSignature | CompositePixelSignature | None,
    allowlist: str,
    recognition_profile: str,
    candidates: Sequence[str] | None,
    with_details: bool,
) -> TemplateMatchResult | tuple[TemplateMatchResult, ...] | list[TextDetection] | PixelMatchResult:
    """把已记录的截图交给所选 common.vision 公开入口。"""
    if mode is RecognitionMode.OPENCV:
        template_inputs, single = _template_inputs(template, roi)
        results = tuple(
            vision.match_template(frame, item, roi=item_roi, confidence=confidence)
            for item, item_roi in template_inputs
        )
        return results[0] if single else results
    if mode is RecognitionMode.OCR:
        return vision.ocr(
            frame,
            roi=roi,
            allowlist=allowlist,
            recognition_profile=recognition_profile,
            candidates=candidates,
        )
    return vision.match_pixels(frame, signature, roi=roi, with_details=with_details)


# -- 内部参数校验 --------------------------------------------------------------


def _validate_retry_options(attempts: int, interval_seconds: float) -> None:
    """校验重试次数和等待间隔，避免生成无法完成的识别流程。

    Args:
        attempts: 最大识别或确认次数。
        interval_seconds: 两次尝试之间的等待秒数。

    Raises:
        ValueError: 参数不满足重试流程的边界约束。
    """
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        raise ValueError('attempts 必须是大于零的整数')
    if isinstance(interval_seconds, bool) or interval_seconds < 0:
        raise ValueError('interval_seconds 不能小于零')


def _has_value(value: _ResultT | None) -> bool:
    """按通用识别结果语义判断默认命中或目标存在。"""
    if value is None:
        return False
    matched = getattr(value, 'matched', None)
    if matched is not None:
        return bool(matched)
    if isinstance(value, (bool, numpy.bool_)):
        return bool(value)
    if isinstance(value, (list, tuple)):
        return any(_has_value(item) for item in value)
    if isinstance(value, (str, bytes, set, frozenset, dict)):
        return bool(value)
    return True


__all__ = [
    'RecognitionMode',
    'RecognitionResult',
    'capture_frame',
    'recognize_with_retry',
    'wait_until_absent',
]
