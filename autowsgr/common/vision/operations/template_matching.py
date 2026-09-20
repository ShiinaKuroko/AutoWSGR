"""模块功能：组合 ROI 裁切、模板加载、缩放和 OpenCV 匹配。

直接调用方：service 入口和需要复用模板匹配的通用模块。

直接依赖：OpenCV 基础执行器、模板配置、system.files 和 NumPy。

边界：不负责设备截图、模板缓存、页面状态或业务领域识别规则。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision.config import (
    OPENCV_TEMPLATE_CONFIDENCE,
    OPENCV_TEMPLATE_SOURCE_RESOLUTION,
)
from autowsgr.common.vision.opencv_engine.executor import OpenCVExecutor


if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np


# ── 模板识别结果模型 ───────────────────────────────────────────────

_log = get_logger('vision.template')


@dataclass(frozen=True, slots=True)
class ROI:
    """以相对坐标描述的矩形区域。"""

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.x1 < self.x2 <= 1.0:
            raise ValueError('ROI 横坐标必须满足 0 <= x1 < x2 <= 1')
        if not 0.0 <= self.y1 < self.y2 <= 1.0:
            raise ValueError('ROI 纵坐标必须满足 0 <= y1 < y2 <= 1')

    def to_absolute(self, width: int, height: int) -> tuple[int, int, int, int]:
        """将相对坐标转换为图片像素坐标。

        Args:
            width: 图片宽度，单位为像素。
            height: 图片高度，单位为像素。

        Returns:
            ``(x1, y1, x2, y2)`` 像素坐标元组。
        """
        return (
            int(self.x1 * width),
            int(self.y1 * height),
            int(self.x2 * width),
            int(self.y2 * height),
        )

    def crop(self, image: np.ndarray) -> np.ndarray:
        """从图片中裁切 ROI。

        Args:
            image: 待裁切的图片数组。

        Returns:
            裁切后的图片副本。
        """
        height, width = image.shape[:2]
        x1, y1, x2, y2 = self.to_absolute(width, height)
        return image[y1:y2, x1:x2].copy()


@dataclass(frozen=True, slots=True)
class Template:
    """一张已加载的模板图片。"""

    name: str
    relative_path: str
    image: np.ndarray
    source_resolution: tuple[int, int] = OPENCV_TEMPLATE_SOURCE_RESOLUTION


@dataclass(frozen=True, slots=True)
class TemplateMatchResult:
    """一次模板匹配结果。"""

    matched: bool
    score: float
    location: tuple[int, int] | None
    template_path: str
    roi: ROI | None = None


class TemplateMatcher:
    """组合模板加载、ROI 裁切、缩放和 OpenCV 匹配。"""

    def __init__(self, executor: OpenCVExecutor | None = None) -> None:
        self._executor = executor or OpenCVExecutor()

    def load_template(
        self,
        relative_path: str | Path,
        *,
        name: str | None = None,
        source_resolution: tuple[int, int] = OPENCV_TEMPLATE_SOURCE_RESOLUTION,
    ) -> Template:
        """加载模板图片并构造模板数据。

        Args:
            relative_path: 模板根目录下的相对路径。
            name: 可选的模板业务名称，默认使用文件名。
            source_resolution: 模板截图分辨率，按 ``(width, height)`` 提供。

        Returns:
            已加载的模板数据。

        Raises:
            ValueError: 路径不是模板根目录下的相对路径。
            FileNotFoundError: 模板文件不存在。
        """
        # 1. 限制模板路径只能指向配置的资源根目录。
        relative = self._relative_path(relative_path)

        # 2. 读取模板图片并保留匹配所需的来源元数据。
        return Template(
            name=name or relative.stem,
            relative_path=relative.as_posix(),
            image=self._executor.load_image(relative),
            source_resolution=source_resolution,
        )

    def match(
        self,
        image: np.ndarray,
        template: Template,
        *,
        roi: ROI | None = None,
        confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
    ) -> TemplateMatchResult:
        """执行模板匹配并返回分数、位置和命中状态。

        Args:
            image: 待搜索的 RGB 或灰度图片数组。
            template: 已加载的模板数据。
            roi: 可选的相对坐标搜索区域。
            confidence: 命中阈值，范围为 ``[0, 1]``。

        Returns:
            包含命中状态、匹配分数、绝对位置和 ROI 的结果。

        Raises:
            ValueError: 置信度超出范围。
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError('匹配置信度必须位于 [0, 1]')

        # 1. 先确定搜索图片和原始尺寸，保证后续坐标使用同一基准。
        image_height, image_width = image.shape[:2]
        search = roi.crop(image) if roi is not None else image
        template_image = template.image
        source_width, source_height = template.source_resolution

        # 2. 截图分辨率变化时，按宽高比例缩放模板。
        if (image_width, image_height) != (source_width, source_height):
            scale_x = image_width / source_width
            scale_y = image_height / source_height
            template_height, template_width = template_image.shape[:2]
            template_image = self._executor.resize(
                template_image,
                max(1, round(template_width * scale_x)),
                max(1, round(template_height * scale_y)),
            )

        # 3. 执行 OpenCV 匹配，并把 ROI 内的位置还原到原图坐标。
        score, location = self._executor.match_template(search, template_image)
        if roi is not None:
            roi_x, roi_y, _, _ = roi.to_absolute(image_width, image_height)
            location = (location[0] + roi_x, location[1] + roi_y)
        return TemplateMatchResult(
            matched=score >= confidence,
            score=score,
            location=location,
            template_path=template.relative_path,
            roi=roi,
        )

    @staticmethod
    def _relative_path(path: str | Path) -> Path:
        """校验并返回模板根目录下的相对路径。"""
        relative = Path(path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('模板路径必须是 OPENCV_TEMPLATE_ROOT 下的相对路径')
        return relative


def load_template(
    relative_path: str | Path,
    *,
    name: str | None = None,
    source_resolution: tuple[int, int] = OPENCV_TEMPLATE_SOURCE_RESOLUTION,
) -> Template:
    """加载模板图片。

    Args:
        relative_path: 模板根目录下的相对路径。
        name: 可选的模板业务名称。
        source_resolution: 模板截图分辨率，按 ``(width, height)`` 提供。

    Returns:
        已加载的模板数据。
    """
    return _MATCHER.load_template(
        relative_path,
        name=name,
        source_resolution=source_resolution,
    )


def match_template(
    image: np.ndarray,
    template: Template,
    *,
    roi: ROI | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
) -> TemplateMatchResult:
    """执行一次模板匹配。

    Args:
        image: 待搜索的 RGB 或灰度图片数组。
        template: 已加载的模板数据。
        roi: 可选的相对坐标搜索区域。
        confidence: 命中阈值，范围为 ``[0, 1]``。

    Returns:
        模板匹配结果。
    """
    result = _MATCHER.match(image, template, roi=roi, confidence=confidence)
    _log.debug(
        '[VISION] 模板匹配 → 匹配结果：template={!r}, score={:.3f}, matched={}',
        result.template_path,
        result.score,
        result.matched,
    )
    return result


def match_templates(
    image: np.ndarray,
    templates: Sequence[Template],
    *,
    roi: ROI | None = None,
    confidence: float = OPENCV_TEMPLATE_CONFIDENCE,
) -> list[TemplateMatchResult]:
    """按顺序匹配一组模板。

    Args:
        image: 待搜索的 RGB 或灰度图片数组。
        templates: 按业务优先级排列的模板序列。
        roi: 可选的相对坐标搜索区域。
        confidence: 命中阈值，范围为 ``[0, 1]``。

    Returns:
        与输入模板顺序一致的匹配结果列表。
    """
    return [
        match_template(image, template, roi=roi, confidence=confidence) for template in templates
    ]


_MATCHER = TemplateMatcher()


__all__ = [
    'ROI',
    'Template',
    'TemplateMatchResult',
    'load_template',
    'match_template',
    'match_templates',
]
