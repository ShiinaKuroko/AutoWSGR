"""模块功能：提供 NumPy 基础数组操作的稳定出口。

上层调用：
- common.vision.adapters.pixel_matching：取用像素采样和坐标换算。

下层依赖：
- common.vision.numpy_engine.executor：提供 NumPy 原子操作。

边界：不定义像素匹配规则，不处理设备截图或业务识别。
"""

from __future__ import annotations

from autowsgr.common.vision.numpy_engine.executor import NumpyExecutor


__all__ = ['NumpyExecutor']
