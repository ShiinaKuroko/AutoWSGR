"""模块功能：组合 NumPy 采样和颜色规则，完成像素签名匹配。

直接调用方：service 入口和需要复用像素签名的通用识别模块。

直接依赖：NumPy 执行器、ROI 模型、像素匹配配置和视觉日志基础设施。

边界：不负责设备截图、页面状态、模板加载或业务领域识别规则。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

import numpy as np

from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision.config import NUMPY_DEFAULT_PIXEL_TOLERANCE
from autowsgr.common.vision.numpy_engine.executor import NumpyExecutor


if TYPE_CHECKING:
    from autowsgr.common.vision.operations.template_matching import ROI


# ── 像素规则模型 ───────────────────────────────────────────────────

_log = get_logger('vision.pixel')


@dataclass(frozen=True, slots=True)
class Color:
    """一个 RGB 颜色。"""

    red: int
    green: int
    blue: int

    def distance(self, other: Color) -> float:
        """计算两个 RGB 颜色的欧几里得距离。

        Args:
            other: 用于比较的 RGB 颜色。

        Returns:
            两个颜色之间的距离。
        """
        return math.sqrt(
            (self.red - other.red) ** 2
            + (self.green - other.green) ** 2
            + (self.blue - other.blue) ** 2,
        )

    def near(self, other: Color, tolerance: float = NUMPY_DEFAULT_PIXEL_TOLERANCE) -> bool:
        """判断两个颜色是否在容差范围内。

        Args:
            other: 用于比较的 RGB 颜色。
            tolerance: 允许的颜色距离。

        Returns:
            颜色距离不超过容差时返回 ``True``。
        """
        return self.distance(other) <= tolerance

    def as_tuple(self) -> tuple[int, int, int]:
        """返回 RGB 整数元组。

        Returns:
            ``(red, green, blue)`` 元组。
        """
        return self.red, self.green, self.blue


@dataclass(frozen=True, slots=True)
class PixelRule:
    """一个相对坐标上的颜色约束。"""

    x: float
    y: float
    color: Color
    tolerance: float = NUMPY_DEFAULT_PIXEL_TOLERANCE

    def __post_init__(self) -> None:
        if not 0.0 <= self.x <= 1.0 or not 0.0 <= self.y <= 1.0:
            raise ValueError('像素规则坐标必须位于 [0, 1]')
        if self.tolerance < 0.0:
            raise ValueError('像素规则容差不能为负数')


class MatchStrategy(StrEnum):
    """像素签名的匹配策略。"""

    ALL = 'all'
    ANY = 'any'
    COUNT = 'count'


@dataclass(frozen=True, slots=True)
class PixelSignature:
    """一组用于识别页面或状态的像素规则。"""

    name: str
    rules: tuple[PixelRule, ...]
    strategy: MatchStrategy = MatchStrategy.ALL
    threshold: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, 'rules', tuple(self.rules))


@dataclass(frozen=True, slots=True)
class CompositePixelSignature:
    """多个像素签名的 OR 组合。"""

    name: str
    signatures: tuple[PixelSignature, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'signatures', tuple(self.signatures))


@dataclass(frozen=True, slots=True)
class PixelDetail:
    """一条像素规则的检测结果。"""

    rule: PixelRule
    actual: Color
    distance: float
    matched: bool


@dataclass(frozen=True, slots=True)
class PixelMatchResult:
    """像素签名匹配结果。"""

    matched: bool
    signature_name: str
    matched_count: int
    total_count: int
    details: tuple[PixelDetail, ...] = field(default_factory=tuple)

    def __bool__(self) -> bool:
        return self.matched

    @property
    def ratio(self) -> float:
        return self.matched_count / self.total_count if self.total_count else 0.0


class PixelMatcher:
    """组合 NumPy 采样、颜色计算和像素规则，完成一次像素匹配。"""

    def __init__(self, executor: NumpyExecutor | None = None) -> None:
        self._executor = executor or NumpyExecutor()

    def match(
        self,
        image: np.ndarray,
        signature: PixelSignature | CompositePixelSignature,
        *,
        roi: ROI | None = None,
        with_details: bool = False,
    ) -> PixelMatchResult:
        """执行一次像素签名匹配。

        Args:
            image: 待检查的 RGB 图片数组。
            signature: 单个像素签名或多个签名的组合。
            roi: 可选的相对坐标检查区域。
            with_details: 是否返回每条规则的采样详情。

        Returns:
            像素签名匹配结果。
        """
        # 1. 先限制检查区域，避免像素规则读取无关画面。
        source = roi.crop(image) if roi is not None else image

        # 2. 组合签名按顺序尝试，单个签名直接执行规则判定。
        if isinstance(signature, CompositePixelSignature):
            return self._match_composite(source, signature, with_details=with_details)
        return self._match_signature(source, signature, with_details=with_details)

    def _match_signature(
        self,
        image: np.ndarray,
        signature: PixelSignature,
        *,
        with_details: bool,
    ) -> PixelMatchResult:
        rules = signature.rules
        # 空规则只在 COUNT 阈值为零时命中，避免无依据地确认状态。
        if not rules:
            matched = signature.strategy is not MatchStrategy.COUNT or signature.threshold == 0
            return PixelMatchResult(matched, signature.name, 0, 0)

        # 3. 批量采样后统一计算颜色距离，保持规则顺序与详情顺序一致。
        actual = self._executor.sample_pixels(image, [(rule.x, rule.y) for rule in rules])
        expected = np.asarray([rule.color.as_tuple() for rule in rules], dtype=np.float32)
        tolerances = np.asarray([rule.tolerance for rule in rules], dtype=np.float32)
        distances = np.sqrt(
            np.sum((actual.astype(np.float32) - expected) ** 2, axis=1),
        )
        matched_flags = distances <= tolerances
        matched_count = int(matched_flags.sum())
        matched = {
            MatchStrategy.ALL: matched_count == len(rules),
            MatchStrategy.ANY: matched_count > 0,
            MatchStrategy.COUNT: matched_count >= signature.threshold,
        }[signature.strategy]
        details = (
            tuple(
                PixelDetail(
                    rule=rule,
                    actual=Color(*(int(channel) for channel in actual[index])),
                    distance=float(distances[index]),
                    matched=bool(matched_flags[index]),
                )
                for index, rule in enumerate(rules)
            )
            if with_details
            else ()
        )
        return PixelMatchResult(matched, signature.name, matched_count, len(rules), details)

    def _match_composite(
        self,
        image: np.ndarray,
        composite: CompositePixelSignature,
        *,
        with_details: bool,
    ) -> PixelMatchResult:
        """依次匹配子签名并在首个命中时返回。

        Args:
            image: 已经完成 ROI 裁切的 RGB 图片数组。
            composite: 按优先级排列的像素签名组合。
            with_details: 是否保留每条规则的采样详情。

        Returns:
            首个命中的组合结果，或包含全部失败详情的未命中结果。
        """
        matched_count = 0
        details: list[PixelDetail] = []
        for signature in composite.signatures:
            result = self._match_signature(image, signature, with_details=with_details)
            matched_count += result.matched_count
            if with_details:
                details.extend(result.details)
            # 组合签名只需要第一个命中结果，后续签名不会改变业务结论。
            if result.matched:
                return PixelMatchResult(
                    True,
                    composite.name,
                    matched_count,
                    len(composite),
                    tuple(details),
                )
        return PixelMatchResult(
            False,
            composite.name,
            matched_count,
            len(composite),
            tuple(details),
        )


def match_pixels(
    image: np.ndarray,
    signature: PixelSignature | CompositePixelSignature,
    *,
    roi: ROI | None = None,
    with_details: bool = False,
) -> PixelMatchResult:
    """执行一次完整的 ROI 和 NumPy 像素签名匹配流程。

    Args:
        image: 待检查的 RGB 图片数组。
        signature: 单个像素签名或多个签名的组合。
        roi: 可选的相对坐标检查区域。
        with_details: 是否返回每条规则的采样详情。

    Returns:
        像素签名匹配结果。
    """
    result = _MATCHER.match(image, signature, roi=roi, with_details=with_details)
    _log.debug(
        '[VISION] 像素匹配 → 匹配结果：signature={!r}, matched_count={}, total_count={}, matched={}',
        result.signature_name,
        result.matched_count,
        result.total_count,
        result.matched,
    )
    return result


_MATCHER = PixelMatcher()


__all__ = [
    'Color',
    'CompositePixelSignature',
    'MatchStrategy',
    'PixelDetail',
    'PixelMatchResult',
    'PixelRule',
    'PixelSignature',
    'match_pixels',
]
