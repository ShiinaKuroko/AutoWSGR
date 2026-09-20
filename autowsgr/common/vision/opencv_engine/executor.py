"""模块功能：执行 OpenCV 图片读取、变换和原子模板匹配。

直接调用方：模板匹配和 OCR 文本预处理等视觉组合操作。

直接依赖：OpenCV、NumPy、system.files 和 vision.config。

边界：不定义模板业务规则、不管理缓存，也不处理设备截图或页面状态。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2

from autowsgr.common.system import files
from autowsgr.common.vision.config import OPENCV_TEMPLATE_ROOT


if TYPE_CHECKING:
    from pathlib import Path

    import numpy as np


class OpenCVExecutor:
    """只提供 OpenCV 和图片文件级操作，不包含模板规则。"""

    # ── 图像读取与变换 ──────────────────────────────────────────────

    @staticmethod
    def load_image(relative_path: Path) -> np.ndarray:
        """从模板根目录加载图片。

        Args:
            relative_path: 模板根目录下的相对图片路径。

        Returns:
            RGB 顺序的图片数组。

        Raises:
            FileNotFoundError: 图片文件不存在。
            ValueError: 路径越界或图片无法解码。
        """
        return files.load_image(
            OPENCV_TEMPLATE_ROOT / relative_path,
            allowed_root=OPENCV_TEMPLATE_ROOT,
        )

    @staticmethod
    def to_gray(image: np.ndarray) -> np.ndarray:
        """将 RGB 图片转换为灰度图。

        Args:
            image: RGB 图片数组，或已经是二维灰度数组。

        Returns:
            二维灰度数组；输入为二维数组时直接返回输入。
        """
        if image.ndim == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    @staticmethod
    def resize(
        image: np.ndarray,
        width: int,
        height: int,
        *,
        interpolation: str = 'area',
    ) -> np.ndarray:
        """将图片缩放到指定尺寸。

        Args:
            image: 待缩放的图片数组。
            width: 目标宽度，单位为像素。
            height: 目标高度，单位为像素。
            interpolation: 插值方式，可选 ``area``、``cubic``、``linear`` 或 ``nearest``。

        Returns:
            缩放后的图片数组。

        Raises:
            ValueError: 尺寸不是正数或插值方式不受支持。
        """
        if width <= 0 or height <= 0:
            raise ValueError('目标图片尺寸必须为正数')
        interpolation_flag = {
            'area': cv2.INTER_AREA,
            'cubic': cv2.INTER_CUBIC,
            'linear': cv2.INTER_LINEAR,
            'nearest': cv2.INTER_NEAREST,
        }.get(interpolation)
        if interpolation_flag is None:
            raise ValueError(f'不支持的插值方式: {interpolation!r}')
        return cv2.resize(image, (width, height), interpolation=interpolation_flag)

    @staticmethod
    def blur(image: np.ndarray, kernel_size: int) -> np.ndarray:
        """执行高斯模糊。

        Args:
            image: 待处理的图片数组。
            kernel_size: 高斯核边长，必须为正奇数。

        Returns:
            模糊后的图片数组。

        Raises:
            ValueError: 高斯核边长不是正奇数。
        """
        if kernel_size <= 0 or kernel_size % 2 == 0:
            raise ValueError('高斯核尺寸必须是正奇数')
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

    @staticmethod
    def normalize(image: np.ndarray) -> np.ndarray:
        """将灰度图归一化到 ``0-255``。

        Args:
            image: 待归一化的灰度数组。

        Returns:
            归一化后的数组。
        """
        return cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)

    @staticmethod
    def threshold(image: np.ndarray) -> np.ndarray:
        """使用 Otsu 算法生成二值图。

        Args:
            image: 待处理的灰度数组。

        Returns:
            二值图片数组。
        """
        return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    @staticmethod
    def gray_to_rgb(image: np.ndarray) -> np.ndarray:
        """将灰度图转换为 RGB 图。

        Args:
            image: 二维灰度数组。

        Returns:
            RGB 顺序的三通道图片数组。
        """
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

    @staticmethod
    def rotate_crop(
        image: np.ndarray,
        center: tuple[float, float],
        size: tuple[int, int],
        angle: float,
    ) -> np.ndarray:
        """围绕绝对像素中心旋转并裁切。

        Args:
            image: 待处理的图片数组。
            center: 旋转和裁切中心，单位为绝对像素。
            size: 裁切尺寸，按 ``(width, height)`` 提供，单位为像素。
            angle: 旋转角度，单位为度。

        Returns:
            旋转后裁切出的图片数组。
        """
        height, width = image.shape[:2]
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, matrix, (width, height))
        return cv2.getRectSubPix(rotated, size, center)

    # ── 模板匹配 ───────────────────────────────────────────────────

    @staticmethod
    def match_template(image: np.ndarray, template: np.ndarray) -> tuple[float, tuple[int, int]]:
        """调用 OpenCV 模板匹配并返回最高分和位置。

        Args:
            image: 待搜索的 RGB 或灰度图片数组。
            template: 待搜索的 RGB 或灰度模板数组。

        Returns:
            最高匹配分数和左上角像素位置；模板大于搜索图片时返回零分和原点。
        """
        search_gray = OpenCVExecutor.to_gray(image)
        template_gray = OpenCVExecutor.to_gray(template)
        # 模板无法放入搜索图时安全返回未命中，避免 OpenCV 抛出尺寸错误。
        if (
            template_gray.shape[0] > search_gray.shape[0]
            or template_gray.shape[1] > search_gray.shape[1]
        ):
            return 0.0, (0, 0)
        matching = cv2.matchTemplate(search_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, score, _, location = cv2.minMaxLoc(matching)
        return float(score), (int(location[0]), int(location[1]))


__all__ = ['OpenCVExecutor']
