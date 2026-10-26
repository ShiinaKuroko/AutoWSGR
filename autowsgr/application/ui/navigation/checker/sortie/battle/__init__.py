"""模块功能：提供普通出征章节检查器的模块入口。

上层调用：
- application.ui.navigation：调用章节事实读取与目标章节到达入口。

下层依赖：
- battle.checker：提供目标章节到达入口。
- battle.recognition：提供章节、地图与掉落计数识别入口。

本模块只导出稳定入口，不放业务实现。
"""

from __future__ import annotations

from autowsgr.application.ui.navigation.checker.sortie.battle.checker import ensure_chapter
from autowsgr.application.ui.navigation.checker.sortie.battle.recognition import (
    read_chapter_number,
    read_chapter_state,
    read_loot_and_ship_count,
    read_map_identity,
)


__all__ = [
    'ensure_chapter',
    'read_chapter_number',
    'read_chapter_state',
    'read_loot_and_ship_count',
    'read_map_identity',
]
