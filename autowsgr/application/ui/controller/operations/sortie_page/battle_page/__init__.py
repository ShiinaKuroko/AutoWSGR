"""模块功能：导出战斗地图页面控制器、面板类型和地图标题解析入口。

上层调用：
- application.ui.navigation：注册地图页面并执行地图回退。
- business.combat、business.logistics：驱动地图面板业务。
- testing.ui：验证地图页面和面板操作。

下层依赖：
- application.ui.controller.operations.sortie_page.battle_page.base：提供地图页面共享操作。
- application.ui.controller.operations.sortie_page.battle_page.page：组合各地图面板 Mixin。
- application.ui.controller.operations.sortie_page.battle_page.data：提供面板和章节数据。
- application.ui.controller.operations.sortie_page.battle_page.recognition：提供地图标题 OCR。
"""

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.battle_page.base import BaseMapPage
from autowsgr.application.ui.controller.operations.sortie_page.battle_page.data import (
    ChapterSlot,
    MapPanel,
    choose_chapter_slot,
)
from autowsgr.application.ui.controller.operations.sortie_page.battle_page.recognition import (
    MapIdentity,
    parse_chapter_label,
    parse_map_title,
)


if TYPE_CHECKING:
    from autowsgr.application.ui.controller.operations.sortie_page.battle_page.page import MapPage


def __getattr__(name: str) -> object:
    """按需加载组合控制器，避免顶部标签 Mixin 与聚合包互相导入。"""
    if name == 'MapPage':
        from autowsgr.application.ui.controller.operations.sortie_page.battle_page.page import (
            MapPage,
        )

        return MapPage
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


__all__ = [
    'BaseMapPage',
    'ChapterSlot',
    'MapIdentity',
    'MapPage',
    'MapPanel',
    'choose_chapter_slot',
    'parse_chapter_label',
    'parse_map_title',
]
