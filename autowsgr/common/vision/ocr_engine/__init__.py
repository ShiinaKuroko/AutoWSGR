"""模块功能：提供 FastOCR 原子执行器和标准化识别结果。

上层调用：
- common.vision.adapters.text_recognition：取用 OCR 识别能力。
- common.vision：导出 TextDetection 数据模型。

下层依赖：
- common.vision.ocr_engine.executor：提供 MaaFramework、OpenCV 和模型配置。

边界：不负责 OCR 文本修正、候选业务规则或页面流程。
"""

from __future__ import annotations

from autowsgr.common.vision.ocr_engine.executor import OCRExecutor, TextDetection


__all__ = ['OCRExecutor', 'TextDetection']
