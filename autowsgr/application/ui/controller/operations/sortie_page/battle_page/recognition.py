"""模块功能：识别地图标题 OCR 文本并解析为地图标识。

上层调用：
- application.ui.controller.operations.sortie_page.battle_page.base：读取当前地图。
- testing.ui：验证地图标题解析和 OCR 结果。

下层依赖：
- application.ui.controller.operations.sortie_page.battle_page.constants：提供标题和章节槽位 OCR 校准。
- application.ui.controller.operations.sortie_page.battle_page.data：提供地图名称数据库和章节范围。
- common.vision：执行 OCR 区域裁剪和文本识别。

本模块只负责 OCR 输入、文本解析和识别结果模型，不执行设备点击、页面导航或业务调度。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import cv2

from autowsgr.application.ui.controller.operations.sortie_page.battle_page.constants import (
    CHAPTER_OCR_ALLOWLIST,
    CHAPTER_SLOT_ROIS,
    TITLE_CROP_REGION,
)
from autowsgr.application.ui.controller.operations.sortie_page.battle_page.data import (
    MAP_DATABASE,
    TOTAL_CHAPTERS,
    ChapterSlot,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import PixelChecker


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.vision import OCREngine


_log = get_logger('ui')


_CHAPTER_NUMERALS: dict[str, int] = {
    '一': 1,
    '二': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '六': 6,
    '七': 7,
    '八': 8,
    '九': 9,
    '十': 10,
}


@dataclass(frozen=True, slots=True)
class MapIdentity:
    """地图标题解析后的章节、关卡和名称。"""

    chapter: int
    map_num: int
    name: str
    raw_text: str


def parse_chapter_label(text: str) -> int | None:
    """解析侧栏章节标签，无法确认时返回 ``None``。"""
    compact = re.sub(r'\s+', '', text)
    if not compact or re.fullmatch(r'[-—_~]+', compact):
        return None

    match = re.fullmatch(r'第?([0-9]{1,2}|[一二三四五六七八九十百]+)章', compact)
    if match is None:
        return None

    token = match.group(1)
    chapter = int(token) if token.isdigit() else _CHAPTER_NUMERALS.get(token)
    if chapter is None or not 1 <= chapter <= TOTAL_CHAPTERS:
        return None
    return chapter


def recognize_chapter_slots(
    screen: np.ndarray,
    ocr: OCREngine,
) -> tuple[ChapterSlot, ...]:
    """从固定侧栏槽位读取章节标签，并在必要时使用二值图复识别。"""
    slots: list[ChapterSlot] = []
    for index, roi in enumerate(CHAPTER_SLOT_ROIS):
        crop = PixelChecker.crop(screen, *roi)
        result = ocr.recognize_single(crop, allowlist=CHAPTER_OCR_ALLOWLIST)
        chapter = parse_chapter_label(result.text)

        if chapter is None and result.text.strip() not in {'', '---'}:
            gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(
                gray,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU,
            )
            binary_rgb = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
            binary_result = ocr.recognize_single(
                binary_rgb,
                allowlist=CHAPTER_OCR_ALLOWLIST,
            )
            binary_chapter = parse_chapter_label(binary_result.text)
            if binary_chapter is not None:
                result = binary_result
                chapter = binary_chapter

        slots.append(
            ChapterSlot(
                index=index,
                chapter=chapter,
                text=result.text.strip(),
                confidence=result.confidence,
            ),
        )

    _log.debug(
        '[UI] 章节槽位: {}',
        [(slot.index, slot.chapter, slot.text, round(slot.confidence, 2)) for slot in slots],
    )
    return tuple(slots)


def parse_map_title(text: str) -> MapIdentity | None:
    """解析地图标题文本，并修正 OCR 粘连的关卡数字。"""
    match = re.search(r'(\d{1,2})\s*[--—]\s*(\d)\s*[/]?\s*(.*)', text)
    if match:
        chapter = int(match.group(1))
        map_num = int(match.group(2))
        name = match.group(3).strip()
        cleaned_name = re.sub(r'^\d+', '', name).strip()

        db_name = MAP_DATABASE.get((chapter, map_num))
        if db_name is not None:
            name = db_name
        elif cleaned_name != name:
            _log.debug(
                "[UI] OCR 名称残留数字: '{}' → '{}'",
                name,
                cleaned_name,
            )
            name = cleaned_name
        return MapIdentity(chapter, map_num, name, text)

    match = re.search(r'(\d+)\s*[--—]\s*(\d+)\s*[/]?\s*(.*)', text)
    if not match:
        return None

    raw_chapter = int(match.group(1))
    raw_map_num = int(match.group(2))
    raw_name = match.group(3).strip()
    if raw_map_num >= 10 and 1 <= raw_chapter <= TOTAL_CHAPTERS:
        candidate = int(str(raw_map_num)[0])
        db_name = MAP_DATABASE.get((raw_chapter, candidate))
        if db_name is not None:
            _log.debug(
                "[UI] OCR 校正: '{}'→{}-{} '{}' (数据库: '{}')",
                text,
                raw_chapter,
                candidate,
                raw_name,
                db_name,
            )
            return MapIdentity(raw_chapter, candidate, db_name, text)

    return MapIdentity(raw_chapter, raw_map_num, raw_name, text)


def recognize_map(screen: np.ndarray, ocr: OCREngine) -> MapIdentity | None:
    """从地图页面截图中识别当前地图标题。"""
    x1, y1, x2, y2 = TITLE_CROP_REGION
    cropped = PixelChecker.crop(screen, x1, y1, x2, y2)
    result = ocr.recognize_maxlen(cropped)
    if not result.text:
        _log.debug('[UI] 地图标题 OCR 无结果')
        return None

    info = parse_map_title(result.text)
    if info is None:
        _log.debug("[UI] 地图标题解析失败: '{}'", result.text)
    else:
        _log.debug(
            '[UI] 地图识别: 第{}章 {}-{} {}',
            info.chapter,
            info.chapter,
            info.map_num,
            info.name,
        )
    return info


__all__ = [
    'MapIdentity',
    'parse_chapter_label',
    'parse_map_title',
    'recognize_chapter_slots',
    'recognize_map',
]
