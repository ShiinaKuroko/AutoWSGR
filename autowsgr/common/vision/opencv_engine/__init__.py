"""模块功能：提供 OpenCV 基础图像操作的稳定出口。

直接调用方：视觉组合操作和需要直接处理图片的通用模块。

直接依赖：executor 中的 OpenCV 原子操作和 system.files 文件边界。

边界：不定义页面匹配规则，不处理设备截图或业务识别。
"""

from __future__ import annotations

from autowsgr.common.vision.opencv_engine.executor import OpenCVExecutor


__all__ = ['OpenCVExecutor']
