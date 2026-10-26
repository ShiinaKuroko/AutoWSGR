"""模块功能：验证导航器的注册表、可达边与算路。

直接调用方：项目测试运行器。

直接依赖：pytest、navigation 的注册中心与页面契约。

边界：只读注册表与算路结果，不点击、不识别、不连接设备。
"""

from __future__ import annotations

import pytest

from autowsgr.application.ui.navigation import registry
from autowsgr.application.ui.navigation.checker import login
from autowsgr.application.ui.navigation.types import NavigationError, PageName


def test_find_path_multi_hop() -> None:
    """跨页路径按广度拼接：回主页必须经过整条每日浮窗链。"""
    path = registry.find_path(PageName.SORTIE_MAP, PageName.EVENT_MAP)

    assert [edge.target for edge in path] == [
        PageName.HOME_NEWS,
        PageName.HOME_REWARD,
        PageName.HOME_REWARD_CONFIRM,
        PageName.HOME,
        PageName.EVENT_MAP,
    ]


def test_find_path_same_page() -> None:
    """起点即目标时返回空路径。"""
    assert registry.find_path(PageName.HOME, PageName.HOME) == ()


def test_find_path_rejects_unreachable() -> None:
    """没有可达路径时抛错。

    用选择舰船页——它有页面名但尚未接入导航图。
    """
    with pytest.raises(NavigationError, match='没有从'):
        registry.find_path(PageName.HOME, PageName.SHIP_SELECTION)


def test_login_pages_register_arrival_checkers() -> None:
    """登录页与区服选择页的确认入口就是各自的 checker。"""
    assert registry.get_checker(PageName.LOGIN_PAGE) is login.check_login_page
    assert registry.get_checker(PageName.SERVER_SELECT) is login.check_server_select


def test_sidebar_pages_and_edges_are_registered() -> None:
    """侧边栏域的六个页面都有确认入口，且各自有出边。"""
    for page in (
        PageName.SIDEBAR,
        PageName.BUILD_SUBMENU,
        PageName.INTENSIFY_SUBMENU,
        PageName.BUILD,
        PageName.INTENSIFY,
        PageName.FRIEND,
    ):
        assert registry.get_checker(page) is not None, page
        assert registry.get_targets(page), page


def test_sidebar_submenus_return_home_without_popup_chain() -> None:
    """侧边栏与两个二级菜单回主页都是一步直达，不经每日浮窗链。"""
    for page in (PageName.SIDEBAR, PageName.BUILD_SUBMENU, PageName.INTENSIFY_SUBMENU):
        path = registry.find_path(page, PageName.HOME)
        assert len(path) == 1, page
        assert path[0].target is PageName.HOME


def test_submenus_lead_to_pages() -> None:
    """两个二级菜单各自通到对应页面。"""
    build_path = registry.find_path(PageName.BUILD_SUBMENU, PageName.BUILD)
    intensify_path = registry.find_path(PageName.INTENSIFY_SUBMENU, PageName.INTENSIFY)

    assert len(build_path) == 1
    assert build_path[0].target is PageName.BUILD
    assert len(intensify_path) == 1
    assert intensify_path[0].target is PageName.INTENSIFY


def test_tabs_are_registered_without_becoming_pages() -> None:
    """标签登记在标签表里，不进确认入口表。"""
    assert set(registry.get_tabs(PageName.SORTIE_MAP)) == {
        'sortie',
        'exercise',
        'expedition',
        'campaign',
        'decisive',
    }
    assert set(registry.get_tabs(PageName.BUILD)) == {'destroy'}
    assert set(registry.get_tabs(PageName.INTENSIFY)) == {'remold', 'skill'}
    assert registry.get_tabs(PageName.HOME) == {}


def test_mission_pages_are_registered() -> None:
    """任务页与「获得」浮窗都有确认入口和出边。"""
    for page in (PageName.MISSION, PageName.MISSION_REWARD_CONFIRM):
        assert registry.get_checker(page) is not None, page
        assert registry.get_targets(page), page


def test_mission_returns_home_through_popup_chain() -> None:
    """任务页回主页要经过每日浮窗链。"""
    path = registry.find_path(PageName.MISSION, PageName.HOME)

    assert [edge.target for edge in path] == [
        PageName.HOME_NEWS,
        PageName.HOME_REWARD,
        PageName.HOME_REWARD_CONFIRM,
        PageName.HOME,
    ]


def test_home_leads_to_mission() -> None:
    """主页一步进任务页。"""
    path = registry.find_path(PageName.HOME, PageName.MISSION)

    assert len(path) == 1
    assert path[0].target is PageName.MISSION


def test_mission_claim_flow_edges() -> None:
    """任务页 → 获得浮窗 → 任务页，两跳都通了。"""
    forward = registry.find_path(PageName.MISSION, PageName.MISSION_REWARD_CONFIRM)
    back = registry.find_path(PageName.MISSION_REWARD_CONFIRM, PageName.MISSION)

    assert len(forward) == 1
    assert forward[0].confirm is False
    assert len(back) == 1
    assert back[0].target is PageName.MISSION


# ── 后院 ────────────────────────────────────────────────────────────────────


def test_backyard_pages_are_registered() -> None:
    """后院主页与四个二级页都有确认入口和出边。"""
    for page in (
        PageName.BACKYARD,
        PageName.CANTEEN,
        PageName.ACADEMY,
        PageName.RANK_ROOM,
        PageName.BATH,
    ):
        assert registry.get_checker(page) is not None, page
        assert registry.get_targets(page), page


def test_rank_skill_list_has_no_checker() -> None:
    """RANK_SKILL_LIST 只占名，无确认入口（三级页后续开发）。"""
    assert registry.get_checker(PageName.RANK_SKILL_LIST) is None
    assert registry.get_targets(PageName.RANK_SKILL_LIST) == ()


def test_home_leads_to_backyard_and_backyard_to_sub_pages() -> None:
    """主页一步进后院，后院一步进任一二级页。"""
    assert len(registry.find_path(PageName.HOME, PageName.BACKYARD)) == 1
    for page in (PageName.CANTEEN, PageName.ACADEMY, PageName.RANK_ROOM, PageName.BATH):
        path = registry.find_path(PageName.BACKYARD, page)
        assert len(path) == 1
        assert path[0].target is page


def test_sub_page_cross_visit_goes_through_backyard() -> None:
    """从军阶室去浴室要经后院主页中转，两跳。"""
    path = registry.find_path(PageName.RANK_ROOM, PageName.BATH)

    assert [edge.target for edge in path] == [PageName.BACKYARD, PageName.BATH]


def test_sub_pages_return_home_through_popup_chain() -> None:
    """建造页、改造页与好友页回主页要经过每日浮窗链。"""
    for page in (PageName.BUILD, PageName.INTENSIFY, PageName.FRIEND):
        path = registry.find_path(page, PageName.HOME)
        assert [edge.target for edge in path] == [
            PageName.HOME_NEWS,
            PageName.HOME_REWARD,
            PageName.HOME_REWARD_CONFIRM,
            PageName.HOME,
        ], page


def test_backyard_sub_pages_return_home_through_popup_chain() -> None:
    """四个二级页回主页都经过每日浮窗链；回后院主页则是一步。"""
    for page in (PageName.CANTEEN, PageName.ACADEMY, PageName.RANK_ROOM, PageName.BATH):
        home_path = registry.find_path(page, PageName.HOME)
        back_path = registry.find_path(page, PageName.BACKYARD)
        assert [edge.target for edge in home_path] == [
            PageName.HOME_NEWS,
            PageName.HOME_REWARD,
            PageName.HOME_REWARD_CONFIRM,
            PageName.HOME,
        ], page
        assert len(back_path) == 1
        assert back_path[0].target is PageName.BACKYARD
