"""模块功能：提供 OpenCV 基础图像操作的稳定出口。

上层调用：
- common.vision.adapters.template_matching 和 text_recognition：取用 OpenCV 图片操作。

下层依赖：
- common.vision.opencv.executor：提供 OpenCV 原子操作。

不定义页面匹配规则，不处理设备截图或业务识别。
"""

from autowsgr.common.vision.opencv.executor import OpenCVExecutor


__all__ = ['OpenCVExecutor']
