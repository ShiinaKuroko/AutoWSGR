"""模块功能：执行 NumPy 图片数组的校验、坐标换算、采样和裁切。

直接调用方：像素匹配等视觉组合操作。

直接依赖：NumPy 和 vision.config 中的相对坐标约束。

边界：只处理数组级操作，不定义像素匹配策略、设备截图或业务识别规则。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from autowsgr.common.vision.config import (
    NUMPY_COORDINATE_MAX,
    NUMPY_COORDINATE_MIN,
)


if TYPE_CHECKING:
    from collections.abc import Sequence


class NumpyExecutor:
    """只提供 NumPy 数组级操作，不包含像素规则。"""

    @staticmethod
    def validate_image(image: np.ndarray) -> tuple[int, int]:
        """验证 RGB 图片数组并返回高度和宽度。

        Args:
            image: 待验证的 RGB 数组，形状至少为 ``H x W x 3``。

        Returns:
            图片高度和宽度。

        Raises:
            ValueError: 图片不是非空的 RGB 数组。
        """
        if image.ndim != 3 or image.shape[2] < 3:
            raise ValueError('视觉图片必须是 HxWx3 的 RGB 数组')
        height, width = image.shape[:2]
        if height == 0 or width == 0:
            raise ValueError('视觉图片不能为空')
        return height, width

    @classmethod
    def coordinate_index(cls, image: np.ndarray, x: float, y: float) -> tuple[int, int]:
        """将相对坐标转换为安全的数组索引。

        Args:
            image: 用于提供尺寸的 RGB 图片数组。
            x: 横向相对坐标，范围为 ``[0, 1]``。
            y: 纵向相对坐标，范围为 ``[0, 1]``。

        Returns:
            以 ``(x, y)`` 顺序返回的整数像素索引。

        Raises:
            ValueError: 图片为空或坐标超出相对坐标范围。
        """
        height, width = cls.validate_image(image)
        if not (
            NUMPY_COORDINATE_MIN <= x <= NUMPY_COORDINATE_MAX
            and NUMPY_COORDINATE_MIN <= y <= NUMPY_COORDINATE_MAX
        ):
            raise ValueError('像素坐标必须位于 [0, 1]')
        return min(int(x * width), width - 1), min(int(y * height), height - 1)

    @classmethod
    def sample_pixel(cls, image: np.ndarray, x: float, y: float) -> tuple[int, int, int]:
        """读取一个相对坐标上的 RGB 像素。

        Args:
            image: 待采样的 RGB 图片数组。
            x: 横向相对坐标，范围为 ``[0, 1]``。
            y: 纵向相对坐标，范围为 ``[0, 1]``。

        Returns:
            ``(red, green, blue)`` 整数元组。

        Raises:
            ValueError: 图片为空或坐标超出相对坐标范围。
        """
        px, py = cls.coordinate_index(image, x, y)
        return tuple(int(channel) for channel in image[py, px, :3])  # type: ignore[return-value]

    @classmethod
    def sample_pixels(
        cls,
        image: np.ndarray,
        positions: Sequence[tuple[float, float]],
    ) -> np.ndarray:
        """批量读取 RGB 像素。

        Args:
            image: 待采样的 RGB 图片数组。
            positions: 按 ``(x, y)`` 顺序提供的相对坐标序列。

        Returns:
            形状为 ``N x 3`` 的 RGB 数组；空坐标序列返回空数组。

        Raises:
            ValueError: 图片为空或坐标格式、坐标范围不正确。
        """
        height, width = cls.validate_image(image)
        coordinates = np.asarray(tuple(positions), dtype=np.float32)
        # 空采样请求返回同形状数组，避免调用方额外分支处理。
        if coordinates.size == 0:
            return np.empty((0, 3), dtype=np.uint8)
        if coordinates.shape != (len(coordinates), 2):
            raise ValueError('像素坐标必须是 (x, y) 序列')
        if np.any(coordinates < NUMPY_COORDINATE_MIN) or np.any(
            coordinates > NUMPY_COORDINATE_MAX,
        ):
            raise ValueError('像素坐标必须位于 [0, 1]')
        xs = np.minimum((coordinates[:, 0] * width).astype(np.intp), width - 1)
        ys = np.minimum((coordinates[:, 1] * height).astype(np.intp), height - 1)
        return image[ys, xs, :3]

    @classmethod
    def crop(
        cls,
        image: np.ndarray,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> np.ndarray:
        """按相对坐标裁切图片数组。

        Args:
            image: 待裁切的 RGB 图片数组。
            x1: 横向起点，范围为 ``[0, 1]``。
            y1: 纵向起点，范围为 ``[0, 1]``。
            x2: 横向终点，必须不小于 ``x1``。
            y2: 纵向终点，必须不小于 ``y1``。

        Returns:
            裁切后的数组副本。

        Raises:
            ValueError: 图片为空或裁切坐标不满足相对坐标约束。
        """
        height, width = cls.validate_image(image)
        if not (
            NUMPY_COORDINATE_MIN <= x1 <= x2 <= NUMPY_COORDINATE_MAX
            and NUMPY_COORDINATE_MIN <= y1 <= y2 <= NUMPY_COORDINATE_MAX
        ):
            raise ValueError('裁切坐标必须满足 0 <= 起点 <= 终点 <= 1')
        return image[int(y1 * height) : int(y2 * height), int(x1 * width) : int(x2 * width)].copy()


__all__ = ['NumpyExecutor']
