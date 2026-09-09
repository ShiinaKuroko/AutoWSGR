"""模块功能：识别战役次数和地图统计结果。

上层调用：
- application.ui.controller.operations.sortie_page.campaign_page.page：传入截图和 OCR 引擎，读取识别结果。

下层依赖：
- application.ui.controller.operations.sortie_page.campaign_page.constants：提供战役次数 OCR 区域。
- common.vision：裁剪 OCR 区域并执行战役统计识别。
- common.vision.map：识别舰船和战利品统计数量。

本模块只负责 OCR 输入、文本解析和识别结果模型，不执行设备点击或页面导航。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.campaign_page import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import PixelChecker
from autowsgr.common.vision.map import (
    LOOT_MAX,
    SHIP_MAX,
    recognize_loot_count,
    recognize_ship_count,
)


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.vision import OCREngine


_log = get_logger('ui')


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


def recognize_campaign_remains(
    screen: np.ndarray,
    ocr: OCREngine | None,
) -> tuple[int, int] | None:
    """从战役页面截图中识别剩余次数和总次数。

    Args:
        screen: 当前战役页面截图。
        ocr: 调用方提供的 OCR 引擎；为空时跳过识别。

    Returns:
        ``(剩余次数, 总次数)``；OCR 不可用或文本无法匹配时返回 ``None``。
    """
    if ocr is None:
        _log.warning('[UI] 无法获取战役次数: 未提供 OCR 引擎')
        return None

    image = PixelChecker.crop(screen, *constants.CAMPAIGN_REMAIN_CROP)
    results = ocr.recognize(image)
    text = ''.join(result.text for result in results).replace(' ', '')
    match = re.search(r'(\d+)[/|](\d+)', text)
    if match:
        remains = int(match.group(1))
        total = int(match.group(2))
        _log.info('[UI] 战役次数识别成功: {}/{}', remains, total)
        return remains, total

    _log.warning('[UI] 战役次数识别失败: OCR 结果未匹配 ({})', text)
    return None


def recognize_acquisition_counts(
    screen: np.ndarray,
    ocr: OCREngine | None,
) -> AcquisitionCounts:
    """从地图截图中识别今日舰船和战利品获取数量。

    Args:
        screen: 当前地图页面截图。
        ocr: 调用方提供的 OCR 引擎；为空时返回空结果。

    Returns:
        获取数量结果；无法识别的字段为 ``None``。
    """
    result = AcquisitionCounts()
    if ocr is None:
        _log.warning('[UI] 未提供 OCR 引擎，无法识别获取数量')
        return result

    result.loot_count = recognize_loot_count(screen, ocr)
    result.ship_count = recognize_ship_count(screen, ocr)
    return result


__all__ = [
    'AcquisitionCounts',
    'recognize_acquisition_counts',
    'recognize_campaign_remains',
]
