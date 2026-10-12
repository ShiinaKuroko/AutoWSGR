"""模块功能：提供后院检查器的模块入口。

上层调用：
- application.ui.navigation：调用后院主页与四个二级页的确认入口。

下层依赖：
- backyard.checker：提供识别入口与入口模板中心。

本模块只导出稳定入口，不放业务实现。
"""

from __future__ import annotations

from autowsgr.application.ui.navigation.checker.backyard.checker import (
    check_academy_page,
    check_backyard_page,
    check_bath_page,
    check_canteen_page,
    check_rank_room_page,
    read_academy_entry_center,
    read_bath_entry_center,
    read_canteen_entry_center,
    read_rank_room_entry_center,
)


__all__ = [
    'check_academy_page',
    'check_backyard_page',
    'check_bath_page',
    'check_canteen_page',
    'check_rank_room_page',
    'read_academy_entry_center',
    'read_bath_entry_center',
    'read_canteen_entry_center',
    'read_rank_room_entry_center',
]
