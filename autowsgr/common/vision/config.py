"""模块功能：集中管理通用视觉算法使用的静态配置。

直接调用方：NumPy、OpenCV 和 FastOCR 执行器及视觉组合操作。

直接依赖：Python 标准库路径能力。

边界：只保存静态参数和资源路径，不加载图像、不执行识别、不持有运行时状态。
"""

from __future__ import annotations

from pathlib import Path


# ── 识别流程默认参数 ───────────────────────────────────────────────

DEFAULT_RECOGNITION_ATTEMPTS = 3
"""一次识别请求的默认最大尝试次数，单位为次。"""

DEFAULT_RECOGNITION_INTERVAL_SECONDS = 0.5
"""相邻两次识别尝试之间的默认等待时间，单位为秒。"""


# ── 模板资源 ───────────────────────────────────────────────────────

OPENCV_TEMPLATE_ROOT = Path(__file__).resolve().parents[3] / 'resources' / 'image'
"""OpenCV 模板图片根目录。"""

OPENCV_TEMPLATE_SOURCE_RESOLUTION = (1280, 720)
"""模板资源的默认采集分辨率，单位为像素。"""

OPENCV_TEMPLATE_CONFIDENCE = 0.85
"""模板匹配默认置信度阈值。"""


# ── NumPy 像素采样 ─────────────────────────────────────────────────

NUMPY_DEFAULT_PIXEL_TOLERANCE = 30.0
"""NumPy 像素规则默认颜色容差。"""

NUMPY_COORDINATE_MIN = 0.0
NUMPY_COORDINATE_MAX = 1.0
"""NumPy 相对坐标边界。"""


# ── OCR 文本预处理 ─────────────────────────────────────────────────

OPENCV_TEXT_SCALE = 4
OPENCV_TEXT_BLUR_KERNEL = 3
"""通用 OCR 文本预处理默认放大倍数和高斯核尺寸。"""


# ── OCR 模型 ───────────────────────────────────────────────────────

OCR_MODEL_FILES = ('det.onnx', 'rec.onnx', 'keys.txt')
"""FastOCR 模型目录中的必需文件。"""

OCR_MODEL_DIR_ENV = 'AUTOWSGR_FASTOCR_MODEL_DIR'
OCR_USER_DIR_ENV = 'AUTOWSGR_FASTOCR_USER_DIR'
OCR_THRESHOLD_ENV = 'AUTOWSGR_FASTOCR_THRESHOLD'
OCR_DEFAULT_THRESHOLD = 0.3
"""FastOCR 模型目录、用户目录和阈值的环境变量配置。"""


__all__ = [
    'DEFAULT_RECOGNITION_ATTEMPTS',
    'DEFAULT_RECOGNITION_INTERVAL_SECONDS',
    'NUMPY_COORDINATE_MAX',
    'NUMPY_COORDINATE_MIN',
    'NUMPY_DEFAULT_PIXEL_TOLERANCE',
    'OCR_DEFAULT_THRESHOLD',
    'OCR_MODEL_DIR_ENV',
    'OCR_MODEL_FILES',
    'OCR_THRESHOLD_ENV',
    'OCR_USER_DIR_ENV',
    'OPENCV_TEMPLATE_CONFIDENCE',
    'OPENCV_TEMPLATE_ROOT',
    'OPENCV_TEMPLATE_SOURCE_RESOLUTION',
    'OPENCV_TEXT_BLUR_KERNEL',
    'OPENCV_TEXT_SCALE',
]
