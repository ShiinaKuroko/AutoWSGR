"""页面识别器注册表。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np

    from autowsgr.common.vision.page_match import PageMatch


_log = get_logger('ui')

_PAGE_REGISTRY: dict[str, Callable[[np.ndarray], PageMatch]] = {}
_DEFAULT_PAGES_REGISTERED: set[str] = set()
_OVERLAY_PAGES: set[str] = set()
"""不遮挡底层识别元素的覆盖型页面。"""


def get_registered_pages() -> list[str]:
    """返回所有已注册的页面名。"""
    return list(_PAGE_REGISTRY.keys())


def register_default_pages() -> None:
    """注册所有页面识别器。"""
    if 'default' in _DEFAULT_PAGES_REGISTERED:
        return

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


def register_page(
    name: str,
    checker: Callable[[np.ndarray], PageMatch],
    *,
    overlay: bool = False,
) -> None:
    """注册一个页面识别器。"""
    key: str = name.value if hasattr(name, 'value') else name
    if key in _PAGE_REGISTRY:
        _log.warning("[UI] 页面 '{}' 已注册，将覆盖", key)
    _PAGE_REGISTRY[key] = checker
    if overlay:
        _OVERLAY_PAGES.add(key)
    else:
        _OVERLAY_PAGES.discard(key)


__all__ = ['get_registered_pages', 'register_default_pages', 'register_page']
