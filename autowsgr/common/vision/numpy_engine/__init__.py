"""模块功能：提供 NumPy 基础数组操作的稳定出口。

直接调用方：视觉组合操作和需要直接采样的通用模块。

直接依赖：executor 中的 NumPy 原子操作。

边界：不定义像素匹配规则，不处理设备截图或业务识别。
"""

from __future__ import annotations

from autowsgr.common.vision.numpy_engine.executor import NumpyExecutor


__all__ = ['NumpyExecutor']
