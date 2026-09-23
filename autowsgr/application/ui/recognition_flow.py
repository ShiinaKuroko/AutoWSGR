"""提供 UI 模块共享的截图、重试识别和终态确认流程。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

import numpy


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.common.device.service import DeviceService


_ResultT = TypeVar('_ResultT')


# -- 公共识别参数 --------------------------------------------------------------

_DEFAULT_RECOGNITION_ATTEMPTS = 3
_DEFAULT_RECOGNITION_INTERVAL_SECONDS = 0.5


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
    recognizer: Callable[[numpy.ndarray], _ResultT | None],
    *,
    record_screenshot: Callable[[numpy.ndarray], None],
    is_match: Callable[[_ResultT | None], bool] | None = None,
    attempts: int = _DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = _DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[_ResultT]:
    """截图并重试识别，返回统一的识别结果。

    Args:
        ctrl: 提供截图能力的设备控制器。
        recognizer: 接收截图并返回识别值的识别器。
        record_screenshot: 接收每次截图的 Context 写入回调。
        is_match: 判断识别值是否命中的谓词；未提供时按通用结果语义判断。
        attempts: 最大识别次数。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        包含最终截图、识别值、命中状态和实际尝试次数的结果。
    """
    _validate_retry_options(attempts, interval_seconds)
    match_predicate = is_match or _has_value

    # 1. 每次识别前都读取最新截图，并按调用方选择写入 Context。
    for attempt in range(1, attempts + 1):
        frame = capture_frame(ctrl, record_screenshot=record_screenshot)
        # 2. 交给调用方识别器判断当前帧，命中后立即返回。
        value = recognizer(frame)
        if match_predicate(value):
            return RecognitionResult(True, True, value, frame, attempt)
        # 3. 未命中时只等待并重试，不在公共层执行点击或抛业务异常。
        if attempt < attempts:
            time.sleep(interval_seconds)

    return RecognitionResult(False, False, value, frame, attempts)


# -- 公共终态确认流程 ----------------------------------------------------------


def wait_until_absent(
    ctrl: DeviceService,
    recognizer: Callable[[numpy.ndarray], _ResultT | None],
    *,
    record_screenshot: Callable[[numpy.ndarray], None],
    is_present: Callable[[_ResultT | None], bool] | None = None,
    attempts: int = _DEFAULT_RECOGNITION_ATTEMPTS,
    interval_seconds: float = _DEFAULT_RECOGNITION_INTERVAL_SECONDS,
) -> RecognitionResult[_ResultT]:
    """截图并重试确认目标消失，不对业务失败抛出页面异常。

    Args:
        ctrl: 提供截图能力的设备控制器。
        recognizer: 接收截图并返回目标识别值的识别器。
        record_screenshot: 接收每次截图的 Context 写入回调。
        is_present: 判断目标是否仍存在的谓词；未提供时按通用结果语义判断。
        attempts: 最大确认次数。
        interval_seconds: 两次确认之间的等待秒数。

    Returns:
        包含最终截图、识别值、目标存在状态和终态确认结果的结果。
    """
    _validate_retry_options(attempts, interval_seconds)
    presence_predicate = is_present or _has_value

    # 1. 每次确认前都读取最新截图，并按调用方选择写入 Context。
    for attempt in range(1, attempts + 1):
        frame = capture_frame(ctrl, record_screenshot=record_screenshot)
        # 2. 交给调用方识别器判断目标是否仍存在。
        value = recognizer(frame)
        # 3. 目标已消失时立即返回成功，避免无意义的后续操作。
        if not presence_predicate(value):
            return RecognitionResult(False, True, value, frame, attempt)
        # 4. 目标仍存在时只等待并重试，把最终失败交给上层处理。
        if attempt < attempts:
            time.sleep(interval_seconds)

    return RecognitionResult(True, False, value, frame, attempts)


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
    if isinstance(value, (str, bytes, list, tuple, set, frozenset, dict)):
        return bool(value)
    return True


__all__ = [
    'RecognitionResult',
    'capture_frame',
    'recognize_with_retry',
    'wait_until_absent',
]
