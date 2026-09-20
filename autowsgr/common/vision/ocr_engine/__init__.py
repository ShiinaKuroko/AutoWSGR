"""模块功能：提供 FastOCR 原子执行器和标准化识别结果。

直接调用方：视觉文字识别组合操作。

直接依赖：executor 中的 MaaFramework、OpenCV 和模型配置。

边界：不负责 OCR 文本修正、候选业务规则或页面流程。
"""

from __future__ import annotations

from autowsgr.common.vision.ocr_engine.executor import OCRExecutor, TextDetection


__all__ = ['OCRExecutor', 'TextDetection']
