"""管理页面识别器的注册和默认页面装载。

`autowsgr.application.ui.navigation.recognition` 读取本文件维护的注册表；默认检查器
来自 `autowsgr.application.ui.pages.backyard_page`、`autowsgr.application.ui.pages.bath_page`、
`autowsgr.application.ui.pages.battle_preparation`、`autowsgr.application.ui.pages.build_page`、
`autowsgr.application.ui.pages.canteen_page`、`autowsgr.application.ui.pages.choose_ship`、
`autowsgr.application.ui.pages.decisive`、`autowsgr.application.ui.pages.event`、
`autowsgr.application.ui.pages.friend_page`、`autowsgr.application.ui.pages.intensify_page`、
`autowsgr.application.ui.pages.main_page`、`autowsgr.application.ui.pages.map`、
`autowsgr.application.ui.pages.mission_page` 和 `autowsgr.application.ui.pages.sidebar_page`；
pytest 可以注册临时检查器。本文件依赖 `autowsgr.common.vision.page_match.PageMatch`、
`autowsgr.common.system.logger.get_logger` 和各页面控制器，不执行截图、点击或路径查找。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np

    from autowsgr.common.vision.page_match import PageMatch


# ── 注册状态 ─────────────────────────────────────────────────

_log = get_logger('ui')

_PAGE_REGISTRY: dict[str, Callable[[np.ndarray], PageMatch]] = {}
_DEFAULT_PAGES_REGISTERED: set[str] = set()
_OVERLAY_PAGES: set[str] = set()
"""不遮挡底层识别元素的覆盖型页面。"""


# ── 注册查询 ─────────────────────────────────────────────────


def get_registered_pages() -> list[str]:
    """返回 `_PAGE_REGISTRY` 中已注册的页面名。"""
    return list(_PAGE_REGISTRY.keys())


# ── 默认页面 ─────────────────────────────────────────────────


def register_default_pages() -> None:
    """加载并注册 `autowsgr.application.ui.pages` 的默认页面识别器。"""
    # 1、已完成注册时直接返回，避免重复导入页面。
    if 'default' in _DEFAULT_PAGES_REGISTERED:
        return

    # 2、按需加载页面检查器并写入注册表。
    from autowsgr.application.ui.pages.backyard_page import BackyardPage
    from autowsgr.application.ui.pages.bath_page import BathPage
    from autowsgr.application.ui.pages.battle_preparation import BattlePreparationPage
    from autowsgr.application.ui.pages.build_page import BuildPage
    from autowsgr.application.ui.pages.canteen_page import CanteenPage
    from autowsgr.application.ui.pages.choose_ship import ChooseShipPage
    from autowsgr.application.ui.pages.decisive import DecisiveBattlePage
    from autowsgr.application.ui.pages.event import BaseEventPage
    from autowsgr.application.ui.pages.friend_page import FriendPage
    from autowsgr.application.ui.pages.intensify_page import IntensifyPage
    from autowsgr.application.ui.pages.main_page import MainPage
    from autowsgr.application.ui.pages.map import MapPage
    from autowsgr.application.ui.pages.mission_page import MissionPage
    from autowsgr.application.ui.pages.sidebar_page import SidebarPage
    from autowsgr.common.types import PageName

    register_page(PageName.MAIN, MainPage.is_current_page)
    register_page(PageName.MAP, MapPage.is_current_page)
    register_page(PageName.BATTLE_PREP, BattlePreparationPage.is_current_page)
    register_page(PageName.MISSION, MissionPage.is_current_page)
    register_page(PageName.BACKYARD, BackyardPage.is_current_page)
    register_page(PageName.BATH, BathPage.is_current_page)
    register_page(PageName.CANTEEN, CanteenPage.is_current_page)
    register_page(PageName.BUILD, BuildPage.is_current_page)
    register_page(PageName.INTENSIFY, IntensifyPage.is_current_page)
    register_page(PageName.FRIEND, FriendPage.is_current_page)
    register_page(PageName.SIDEBAR, SidebarPage.is_current_page, overlay=True)
    register_page(PageName.EVENT_MAP, BaseEventPage.is_current_page)
    register_page(PageName.DECISIVE_BATTLE, DecisiveBattlePage.is_current_page)
    register_page(PageName.CHOOSE_SHIP, ChooseShipPage.is_current_page)
    _DEFAULT_PAGES_REGISTERED.add('default')


# ── 自定义页面 ─────────────────────────────────────────────────


def register_page(
    name: str,
    checker: Callable[[np.ndarray], PageMatch],
    *,
    overlay: bool = False,
) -> None:
    """把页面检查器注册到 `_PAGE_REGISTRY`。"""
    key: str = name.value if hasattr(name, 'value') else name
    if key in _PAGE_REGISTRY:
        _log.warning("[UI] 页面 '{}' 已注册，将覆盖", key)
    _PAGE_REGISTRY[key] = checker
    if overlay:
        _OVERLAY_PAGES.add(key)
    else:
        _OVERLAY_PAGES.discard(key)


__all__ = ['get_registered_pages', 'register_default_pages', 'register_page']
