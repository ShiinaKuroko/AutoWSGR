"""战斗页面的通用视觉识别原语。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from autowsgr.application.vision.calibration.combat import (
    ENEMY_SCAN_AREAS,
    FORMATION_ALLOWLIST,
    FORMATION_NAMES,
    FORMATION_ROI,
    RESULT_BLOOD_BAR_PROBE,
    SHIP_DROP_PAGE_SIGNATURE,
    SHIP_NAME_CROP,
    SHIP_SLOT_Y,
    SHIP_TYPE_CROP,
)
from autowsgr.application.vision.native import ApiDll, get_api_dll
from autowsgr.application.vision.ship_list import recognize_ship_name
from autowsgr.common import vision
from autowsgr.common.system import get_logger
from autowsgr.common.vision._resources.combat import CombatTemplates
from autowsgr.common.vision._resources.keys import TemplateKey


if TYPE_CHECKING:
    from autowsgr.common.device import AndroidController


_log = get_logger('combat.recognition')


def recognize_enemy_ships(
    screen: np.ndarray,
    mode: str = 'fight',
    *,
    dll: ApiDll | None = None,
) -> dict[str, int]:
    """从六个舰种图标统计敌方舰种。"""
    if dll is None:
        dll = get_api_dll()
    areas = ENEMY_SCAN_AREAS.get(mode)
    if areas is None:
        raise ValueError(f'不支持的模式: {mode!r}，可选: {list(ENEMY_SCAN_AREAS)}')
    image = np.asarray(Image.fromarray(screen).convert('L').resize((960, 540)))
    crops = [image[top:bottom, left:right] for left, top, right, bottom in areas]
    result = dll.recognize_enemy(crops)
    _log.debug('[识别] DLL 返回: {}', result)
    counts: dict[str, int] = {}
    for ship_type in result.split():
        if ship_type != 'NO':
            counts[ship_type] = counts.get(ship_type, 0) + 1
    counts['ALL'] = sum(counts.values())
    _log.debug('[识别] 敌方编成: {}', counts)
    return counts


def recognize_enemy_formation(screen: np.ndarray, ocr: object) -> str:
    """从索敌截图 OCR 识别敌方阵型文本。"""
    text = vision.read(
        screen,
        reader=ocr,
        roi=FORMATION_ROI,
        mode=vision.ReadMode.SINGLE,
        allowlist=FORMATION_ALLOWLIST,
    ).text.strip()
    if not text:
        _log.debug('[识别] 阵型 OCR 无结果')
        return ''
    for key, name in FORMATION_NAMES.items():
        if key in text:
            _log.info('[识别] 敌方阵型: {}', name)
            return name
    _log.info('[识别] 敌方阵型 (原文): {}', text)
    return text


@dataclass(frozen=True, slots=True)
class ShipDropResult:
    """舰船掉落 OCR 的技术结果。"""

    ship_name: str | None
    ship_type: str | None


def recognize_ship_drop(screen: np.ndarray, ocr: object) -> ShipDropResult:
    """从掉落页的旋转文本区域识别舰名和舰种。"""
    name = recognize_ship_name(vision.crop_rotated(screen, *SHIP_NAME_CROP), ocr)
    _log.debug('[识别] 掉落舰名: {}', name or '未识别')
    ship_type = (
        vision.read(
            vision.crop_rotated(screen, *SHIP_TYPE_CROP),
            reader=ocr,
            mode=vision.ReadMode.SINGLE,
        ).text.strip()
        or None
    )
    _log.debug('[识别] 掉落舰种: {}', ship_type or '未识别')
    return ShipDropResult(ship_name=name, ship_type=ship_type)


def detect_mvp(screen: np.ndarray, confidence: float = 0.8) -> int | None:
    """从结算页模板位置推算 MVP 槽位。"""
    detail = vision.match(screen, CombatTemplates.MVP_BADGE, confidence=confidence).best
    if detail is None:
        _log.debug('[识别] 未检测到 MVP 徽章')
        return None
    slot = min(range(len(SHIP_SLOT_Y)), key=lambda i: abs(detail.center[1] - SHIP_SLOT_Y[i]))
    _log.info('[识别] MVP 位置: {} (conf={:.3f})', slot + 1, detail.confidence)
    return slot + 1


def image_exist(
    device: AndroidController, template_key: TemplateKey | str, confidence: float
) -> bool:
    """检查当前截图是否包含模板。"""
    key = TemplateKey(template_key) if isinstance(template_key, str) else template_key
    return bool(vision.match(device.screenshot(), key.templates, confidence=confidence))


def get_enemy_info(device: AndroidController, mode: str = 'fight') -> dict[str, int]:
    return recognize_enemy_ships(device.screenshot(), mode=mode)


def get_enemy_formation(device: AndroidController, ocr_engine: object) -> str:
    return recognize_enemy_formation(device.screenshot(), ocr_engine) if ocr_engine else ''


def get_ship_drop(device: AndroidController, ocr: object) -> str | None:
    """有限重试读取掉落舰名。"""
    for attempt in range(5):
        if attempt:
            time.sleep(0.5)
        result = recognize_ship_drop(device.screenshot(), ocr)
        if result.ship_name:
            _log.info('[Combat] 掉落识别: {} ({})', result.ship_name, result.ship_type or '未知')
            return result.ship_name
        _log.debug('[Combat] 掉落 OCR 第 {}/5 次未识别', attempt + 1)
    return None


__all__ = [
    'RESULT_BLOOD_BAR_PROBE',
    'SHIP_DROP_PAGE_SIGNATURE',
    'ShipDropResult',
    'detect_mvp',
    'get_enemy_formation',
    'get_enemy_info',
    'get_ship_drop',
    'image_exist',
    'recognize_enemy_formation',
    'recognize_enemy_ships',
    'recognize_ship_drop',
]
