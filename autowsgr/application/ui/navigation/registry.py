"""管理页面识别器的注册和默认页面装载。

`autowsgr.application.ui.navigation.recognition` 读取本文件维护的注册表；默认检查器
来自 `autowsgr.application.ui.controller.backyard.main_page`、`autowsgr.application.ui.controller.backyard.bath_page`、
`autowsgr.application.ui.controller.fleet`、`autowsgr.application.ui.controller.sidebar.build_page`、
`autowsgr.application.ui.controller.backyard.canteen_page`、
`autowsgr.application.ui.controller.operations.sortie_page.decisive_page`、`autowsgr.application.ui.controller.home.event_page`、
`autowsgr.application.ui.controller.sidebar.friend_page`、`autowsgr.application.ui.controller.sidebar.intensify_page`、
`autowsgr.application.ui.controller.home.main_page`、`autowsgr.application.ui.controller.operations.sortie_page.battle_page`、
`autowsgr.application.ui.controller.operations.mission_page` 和 `autowsgr.application.ui.controller.sidebar.main_page`；
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
    """加载并注册 `autowsgr.application.ui.controller` 的默认页面识别器。"""
    # 1、已完成注册时直接返回，避免重复导入页面。
    if 'default' in _DEFAULT_PAGES_REGISTERED:
        return

    # 2、按需加载页面检查器并写入注册表。
    from autowsgr.application.ui.controller.backyard.bath_page import BathPage
    from autowsgr.application.ui.controller.backyard.canteen_page import CanteenPage
    from autowsgr.application.ui.controller.backyard.main_page import BackyardPage
    from autowsgr.application.ui.controller.fleet import (
        BattlePreparationPage,
        check_ship_selection_page,
    )
    from autowsgr.application.ui.controller.home.event_page import BaseEventPage
    from autowsgr.application.ui.controller.home.main_page import HomePage
    from autowsgr.application.ui.controller.operations.mission_page import MissionPage
    from autowsgr.application.ui.controller.operations.sortie_page.decisive_page import (
        DecisiveBattlePage,
    )
    from autowsgr.application.ui.controller.operations.sortie_page.main_page import SortiePage
    from autowsgr.application.ui.controller.sidebar.build_page import BuildPage
    from autowsgr.application.ui.controller.sidebar.friend_page import FriendPage
    from autowsgr.application.ui.controller.sidebar.intensify_page import IntensifyPage
    from autowsgr.application.ui.controller.sidebar.main_page import SidebarPage
    from autowsgr.common.types import PageName

    register_page(PageName.HOME, HomePage.check_current_page)
    register_page(PageName.MAP, SortiePage.check_current_page)
    register_page(PageName.BATTLE_PREP, BattlePreparationPage.check_current_page)
    register_page(PageName.MISSION, MissionPage.check_current_page)
    register_page(PageName.BACKYARD, BackyardPage.check_current_page)
    register_page(PageName.BATH, BathPage.check_current_page)
    register_page(PageName.CANTEEN, CanteenPage.check_current_page)
    register_page(PageName.BUILD, BuildPage.check_current_page)
    register_page(PageName.INTENSIFY, IntensifyPage.check_current_page)
    register_page(PageName.FRIEND, FriendPage.check_current_page)
    register_page(PageName.SIDEBAR, SidebarPage.check_current_page, overlay=True)
    register_page(PageName.EVENT_MAP, BaseEventPage.check_current_page)
    register_page(PageName.DECISIVE_BATTLE, DecisiveBattlePage.check_current_page)
    register_page(PageName.CHOOSE_SHIP, check_ship_selection_page)
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
