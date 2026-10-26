"""模块功能：把出征页画面解释为章节、地图和掉落计数事实。

上层调用：
- application.ui.navigation.checker.sortie.battle.checker：读取章节状态与地图身份。
- business.combat.bettle：读取今日掉落与舰船数量。

下层依赖：
- checker.sortie.battle.constants：提供地图数据与识别区域。
- application.vision.sortie_recognition：读取掉落与舰船数量。
- common.system.logger：记录识别事实。
- common.vision：提供像素裁剪与 OCR 结果类型。

边界：只读取识别事实，不点击设备、不等待页面、不决定章节落点。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import cv2

from autowsgr.application.ui.navigation.checker.sortie.battle import constants
from autowsgr.application.vision.sortie_recognition import (
    LootShipCount,
    recognize_loot_count,
    recognize_ship_count,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import PixelChecker


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.vision import OCREngine
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 识别参数 ─────────────────────────────────────────────────────────────────

# 章节标签 OCR 允许字符，限制识别范围避免把侧栏其他文字读成章号。
CHAPTER_OCR_ALLOWLIST = '0123456789第章一二三四五六七八九十'

# 侧栏中间槽位，用作当前章节的锚点。
CHAPTER_SLOT_CENTER_INDEX = 2

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


# ── 识别事实模型 ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class MapIdentity:
    """地图标题解析后的章节、关卡和名称。"""

    chapter: int
    map_num: int
    name: str
    raw_text: str


@dataclass(frozen=True, slots=True)
class ChapterSlot:
    """一个固定章节槽位的 OCR 结果和页面索引。"""

    index: int
    chapter: int | None
    text: str
    confidence: float


# ── 章节识别入口 ─────────────────────────────────────────────────────────────


def read_chapter_state(
    ctx: ContextHandle,
) -> tuple[tuple[ChapterSlot, ...], int | None]:
    """用一帧截图读出侧栏槽位和当前章节。

    槽位与标题必须在同一帧读取：章节切换动画期间两帧的章号可能不一致。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        按页面顺序排列的章节槽位，以及确认到的当前章节编号；无法确认时为 None。

    Raises:
        RuntimeError: OCR 引擎未注入。
    """
    screen = ctx.runtime.ctrl.screenshot()
    ocr = _require_ocr(ctx)
    slots = _recognize_chapter_slots(screen, ocr)
    title = _recognize_map(screen, ocr)

    current = slots[CHAPTER_SLOT_CENTER_INDEX].chapter
    if current is None and title is not None:
        current = title.chapter
    if current is not None and title is not None and title.chapter != current:
        _log.warning(
            '[UI] 章节状态不一致：侧栏第{}章，标题第{}章',
            current,
            title.chapter,
        )
    return slots, current


def read_chapter_number(ctx: ContextHandle) -> int | None:
    """读取当前章节编号。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        当前章节编号；槽位读不到时退回地图标题，仍无法确认时为 None。
    """
    _slots, current = read_chapter_state(ctx)
    return current


def read_map_identity(ctx: ContextHandle) -> MapIdentity | None:
    """读取当前地图标题解析出的章节、关卡和名称。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        当前地图的结构化标识；标题为空或无法解析时为 None。

    Raises:
        RuntimeError: OCR 引擎未注入。
    """
    screen = ctx.runtime.ctrl.screenshot()
    return _recognize_map(screen, _require_ocr(ctx))


def read_loot_and_ship_count(
    ctx: ContextHandle,
    *,
    read_loot: bool = True,
) -> LootShipCount:
    """读取出征页的战利品与舰船数量。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        read_loot: 是否同时读取战利品数量。

    Returns:
        读取到的战利品和舰船数量，未识别的项目为 None。

    Raises:
        RuntimeError: OCR 引擎未注入。
    """
    screen = ctx.runtime.ctrl.screenshot()
    ocr = _require_ocr(ctx)
    loot = recognize_loot_count(screen, ocr) if read_loot else None
    ship = recognize_ship_count(screen, ocr)
    return LootShipCount(loot=loot, ship=ship)


# ── 章节槽位识别 ─────────────────────────────────────────────────────────────


def _recognize_chapter_slots(
    screen: np.ndarray,
    ocr: OCREngine,
) -> tuple[ChapterSlot, ...]:
    """从固定侧栏槽位读取章节标签，必要时用二值图复识别。

    Args:
        screen: 出征页 RGB 截图。
        ocr: OCR 引擎。

    Returns:
        按页面顺序排列的章节槽位识别结果。
    """
    slots: list[ChapterSlot] = []
    for index, roi in enumerate(constants.CHAPTER_SLOT_ROIS):
        crop = PixelChecker.crop(screen, *roi)
        result = ocr.recognize_single(crop, allowlist=CHAPTER_OCR_ALLOWLIST)
        chapter = _parse_chapter_label(result.text)

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
            binary_chapter = _parse_chapter_label(binary_result.text)
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
        '[UI] 章节槽位：{}',
        [(slot.index, slot.chapter, slot.text, round(slot.confidence, 2)) for slot in slots],
    )
    return tuple(slots)


def _parse_chapter_label(text: str) -> int | None:
    """解析侧栏章节标签。

    Args:
        text: 章节标签 OCR 文本。

    Returns:
        章节编号；文本格式不符合征战页章节规则时为 None。
    """
    compact = re.sub(r'\s+', '', text)
    if not compact or re.fullmatch(r'[-—_~]+', compact):
        return None

    match = re.fullmatch(r'第?([0-9]{1,2}|[一二三四五六七八九十百]+)章', compact)
    if match is None:
        return None

    token = match.group(1)
    chapter = int(token) if token.isdigit() else _CHAPTER_NUMERALS.get(token)
    if chapter is None or not 1 <= chapter <= constants.TOTAL_CHAPTERS:
        return None
    return chapter


# ── 地图标题识别 ─────────────────────────────────────────────────────────────


def _recognize_map(screen: np.ndarray, ocr: OCREngine) -> MapIdentity | None:
    """从截图的地图标题读出章节、关卡和名称。

    Args:
        screen: 出征页 RGB 截图。
        ocr: OCR 引擎。

    Returns:
        当前地图的结构化标识；标题为空或无法解析时为 None。
    """
    x1, y1, x2, y2 = constants.TITLE_CROP_REGION
    cropped = PixelChecker.crop(screen, x1, y1, x2, y2)
    result = ocr.recognize_maxlen(cropped)
    if not result.text:
        _log.debug('[UI] 地图标题 OCR 无结果')
        return None

    info = _parse_map_title(result.text)
    if info is None:
        _log.debug("[UI] 地图标题解析失败：'{}'", result.text)
    else:
        _log.debug(
            '[UI] 地图识别：第{}章 {}-{} {}',
            info.chapter,
            info.chapter,
            info.map_num,
            info.name,
        )
    return info


def _parse_map_title(text: str) -> MapIdentity | None:
    """解析地图标题文本，并修正 OCR 粘连的关卡数字。

    Args:
        text: 地图标题 OCR 文本。

    Returns:
        结构化地图标识；无法解析章节和地图编号时为 None。
    """
    match = re.search(r'(\d{1,2})\s*[--—]\s*(\d)\s*[/]?\s*(.*)', text)
    if match:
        chapter = int(match.group(1))
        map_num = int(match.group(2))
        name = match.group(3).strip()
        cleaned_name = re.sub(r'^\d+', '', name).strip()

        db_name = constants.MAP_DATABASE.get((chapter, map_num))
        if db_name is not None:
            name = db_name
        elif cleaned_name != name:
            _log.debug(
                "[UI] OCR 名称残留数字：'{}' → '{}'",
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
    if raw_map_num >= 10 and 1 <= raw_chapter <= constants.TOTAL_CHAPTERS:
        candidate = int(str(raw_map_num)[0])
        db_name = constants.MAP_DATABASE.get((raw_chapter, candidate))
        if db_name is not None:
            _log.debug(
                "[UI] OCR 校正：'{}'→{}-{} '{}' (数据库: '{}')",
                text,
                raw_chapter,
                candidate,
                raw_name,
                db_name,
            )
            return MapIdentity(raw_chapter, candidate, db_name, text)

    return MapIdentity(raw_chapter, raw_map_num, raw_name, text)


# ── 识别前置条件 ─────────────────────────────────────────────────────────────


def _require_ocr(ctx: ContextHandle) -> OCREngine:
    """返回上下文绑定的 OCR 引擎。

    Args:
        ctx: 提供运行时服务引用的 dispatch 上下文句柄。

    Returns:
        当前任务绑定的 OCR 引擎。

    Raises:
        RuntimeError: 任务没有绑定 OCR 引擎。
    """
    ocr = ctx.runtime.ocr
    if ocr is None:
        raise RuntimeError('需要 OCR 引擎才能识别出征页章节')
    return ocr


__all__ = [
    'ChapterSlot',
    'MapIdentity',
    'read_chapter_number',
    'read_chapter_state',
    'read_loot_and_ship_count',
    'read_map_identity',
]
