"""应用层的舰种文字解析和选船列表兼容入口。"""

from __future__ import annotations

import re

from autowsgr.common.vision.ship_list import (  # noqa: F401
    LEGACY_HEIGHT,
    LEGACY_LIST_WIDTH,
    LEGACY_WIDTH,
    LevelOCRRetryNeededError,
    _parse_level_with_status,
    _probe_level_near_name,
    locate_ship_rows,
    read_ship_level_at_card,
    recognize_ships_in_list,
    to_legacy_format,
)
from autowsgr.types import ShipType


def extract_ship_type_from_text(text: str) -> ShipType | None:
    """从 OCR 文本提取游戏舰种枚举。"""
    if not text:
        return None
    normalized = re.sub(r'[（(][^（()）]*[)）]', '', text).replace(' ', '')
    for ship_type in ShipType:
        if ship_type is not ShipType.Other and ship_type.value in normalized:
            return ship_type
    return None


__all__ = [
    'LEGACY_HEIGHT',
    'LEGACY_LIST_WIDTH',
    'LEGACY_WIDTH',
    'LevelOCRRetryNeededError',
    'extract_ship_type_from_text',
    'locate_ship_rows',
    'read_ship_level_at_card',
    'recognize_ships_in_list',
    'to_legacy_format',
]
