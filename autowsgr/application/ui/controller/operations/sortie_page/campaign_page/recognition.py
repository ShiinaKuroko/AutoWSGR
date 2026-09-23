"""模块功能：识别战役页面的难度、剩余次数和出征统计。

上层调用：
- application.ui.controller.operations.sortie_page.campaign_page.page：读取战役页面事实。
- testing.ui：验证战役页面识别结果。

下层依赖：
- application.ui.controller.operations.sortie_page.campaign_page.constants：提供难度探测坐标。
- common.vision：提供像素读取和 OCR 区域裁剪。
- common.vision.map：提供舰船和战利品数量识别。

边界：
只读取截图并构造识别结果，不执行设备点击、页面导航或运行时上下文创建。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.campaign_page import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision.operations.pixel_matching import Color
from autowsgr.common.vision import PixelChecker
from autowsgr.application.vision.sortie_recognition import (
    LOOT_MAX,
    SHIP_MAX,
    recognize_loot_count,
    recognize_ship_count,
)


if TYPE_CHECKING:
    import numpy

    from autowsgr.common.vision import OCREngine


_log = get_logger('ui.campaign_page')


# ── 页面识别校准 ────────────────────────────────────────────────────────────────────

# 难度按钮同一探测点的蓝色表示困难状态，红褐色表示简单状态。
_DIFFICULTY_HARD_COLOR = Color.from_rgb_tuple((29, 139, 234))
_DIFFICULTY_EASY_COLOR = Color.from_rgb_tuple((141, 46, 52))
_DIFFICULTY_COLOR_TOLERANCE: float = 50.0

# 次数 OCR 区域按归一化坐标 (x1, y1, x2, y2) 保存。
_CAMPAIGN_REMAIN_CROP: tuple[float, float, float, float] = (
    0.0800,
    0.8200,
    0.2500,
    0.9200,
)


# ── 识别结果 ──────────────────────────────────────────────────────────────────────


@dataclass
class AcquisitionCounts:
    """今日舰船和战利品获取数量。"""

    ship_count: int | None = None
    """今日已获取舰船数量。"""
    ship_max: int = SHIP_MAX
    """今日舰船获取上限。"""
    loot_count: int | None = None
    """今日已获取战利品数量。"""
    loot_max: int = LOOT_MAX
    """今日战利品获取上限。"""


def recognize_difficulty(screen: numpy.ndarray) -> str | None:
    """从难度按钮颜色识别当前战役难度。

    Args:
        screen: 当前战役页面 RGB 截图。

    Returns:
        当前难度，无法确认时返回 None。
    """
    pixel = PixelChecker.get_pixel(screen, *constants.CLICK_DIFFICULTY)
    if pixel.near(_DIFFICULTY_HARD_COLOR, tolerance=_DIFFICULTY_COLOR_TOLERANCE):
        return 'hard'
    if pixel.near(_DIFFICULTY_EASY_COLOR, tolerance=_DIFFICULTY_COLOR_TOLERANCE):
        return 'easy'
    return None


def recognize_campaign_remains(
    screen: numpy.ndarray,
    ocr_engine: OCREngine | None,
) -> tuple[int, int] | None:
    """从战役页面截图中识别剩余次数和总次数。

    Args:
        screen: 当前战役页面截图。
        ocr_engine: 调用方提供的 OCR 引擎；为空时跳过识别。

    Returns:
        ``(剩余次数, 总次数)``；OCR 不可用或文本无法匹配时返回 None。
    """
    if ocr_engine is None:
        _log.warning('[UI] 战役页面 → 识别次数：结果=缺少 OCR')
        return None

    image = PixelChecker.crop(screen, *_CAMPAIGN_REMAIN_CROP)
    results = ocr_engine.recognize(image)
    ocr_text = ''.join(result.text for result in results).replace(' ', '')
    match = re.search(r'(\d+)[/|](\d+)', ocr_text)
    if match:
        remains = int(match.group(1))
        total = int(match.group(2))
        _log.debug(
            '[UI] 战役页面 → 识别次数：结果=成功，剩余次数={}，总次数={}',
            remains,
            total,
        )
        return remains, total

    _log.warning('[UI] 战役页面 → 识别次数：结果=失败，文本={!r}', ocr_text)
    return None


def recognize_acquisition_counts(
    screen: numpy.ndarray,
    ocr_engine: OCREngine | None,
) -> AcquisitionCounts:
    """从出征页面截图中识别今日舰船和战利品获取数量。

    Args:
        screen: 当前出征页面截图。
        ocr_engine: 调用方提供的 OCR 引擎；为空时返回空结果。

    Returns:
        获取数量结果；无法识别的字段为 None。
    """
    result = AcquisitionCounts()
    if ocr_engine is None:
        _log.warning('[UI] 出征页面 → 识别获取数量：结果=缺少 OCR')
        return result

    result.loot_count = recognize_loot_count(screen, ocr_engine)
    result.ship_count = recognize_ship_count(screen, ocr_engine)
    _log.debug(
        '[UI] 出征页面 → 识别获取数量：舰船数量={}，战利品数量={}',
        result.ship_count,
        result.loot_count,
    )
    return result


__all__ = [  # noqa: RUF022
    'AcquisitionCounts',
    'recognize_difficulty',
    'recognize_campaign_remains',
    'recognize_acquisition_counts',
]
