"""模块功能：计算设备输入操作的前置随机延迟。

上层调用：
- common.device.scrcpy_engine.executor：初始化延迟范围，并在需要延迟的输入动作前取值。

下层依赖：
- Python 标准库 random 和 math。

边界：只维护当前进程的延迟范围，不解析用户配置、不执行 sleep 或设备操作。
"""

from __future__ import annotations

import math
import random


# 当前进程的随机延迟范围，由 configure_operation_delay_bounds 在会话初始化时写入。
_operation_delay_bounds = [0.0, 0.0]


def configure_operation_delay_bounds(minimum: float, maximum: float) -> None:
    """更新设备操作前的随机延迟范围。

    Args:
        minimum: 延迟下界，单位为秒。
        maximum: 延迟上界，单位为秒。

    Raises:
        ValueError: 延迟不是有限数，或下界大于上界。
    """
    if not math.isfinite(minimum) or not math.isfinite(maximum):
        raise ValueError('设备操作延迟必须是有限数')
    if minimum < 0 or minimum > maximum:
        raise ValueError('设备操作延迟范围必须满足 0 <= minimum <= maximum')
    _operation_delay_bounds[0] = minimum
    _operation_delay_bounds[1] = maximum


def calculate_operation_delay() -> float:
    """计算本次设备操作前应等待的随机延迟秒数。"""
    return random.uniform(
        _operation_delay_bounds[0],
        _operation_delay_bounds[1],
    )


__all__ = ['calculate_operation_delay', 'configure_operation_delay_bounds']
