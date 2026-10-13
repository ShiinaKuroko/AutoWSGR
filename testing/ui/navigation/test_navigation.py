"""模块功能：验证导航器的路径拼接、确认、浮窗链与回退。

直接调用方：项目测试运行器。

直接依赖：pytest、navigation 的注册中心与入口、dispatch 会话状态。

边界：用替身接管设备点击与页面确认，不连接设备、不识别画面。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from autowsgr.application.ui.controller.home.main_page import constants as home_constants
from autowsgr.application.ui.controller.login import constants as login_constants
from autowsgr.application.ui.navigation import registry
from autowsgr.application.ui.navigation.executor import NavigationExecutor
from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    constants as sortie_constants,
)
from autowsgr.application.ui.navigation.checker import home, login, sidebar
from autowsgr.application.ui.navigation import executor as executor_module
from autowsgr.application.ui.navigation.types import NavTab, NavTarget
from autowsgr.application.ui.navigation.service import NavigationService
from autowsgr.application.ui.navigation.types import NavigationError, PageName
from autowsgr.dispatch.session import SessionState


class _Ctrl:
    """设备服务替身，记录点击落点。"""

    def __init__(self) -> None:
        self.clicks: list[tuple[float, float]] = []

    def click(self, x: float, y: float, *, delay: bool = False) -> None:  # noqa: ARG002
        self.clicks.append((x, y))


def _ctx() -> Any:
    """构造带活动任务参数的上下文替身。"""
    return SimpleNamespace(
        runtime=SimpleNamespace(ctrl=_Ctrl()),
        read_event_type=lambda: 'stage_push',
        read_event_stage=lambda: 'EX7',
    )


def _accept_path(monkeypatch: pytest.MonkeyPatch, target: PageName) -> None:
    """只让目标页的确认入口命中，并让三个每日浮窗视为不存在。

    替身跟着 `absent` 翻转：后识别问的是「这一页还在不在」，从更深的层退回时
    出发页必须判为已经收起。链路上 `confirm=False` 的中间步不做到达确认，
    因此只需要最终目标命中。
    """
    for page in list(registry._PAGE_CHECKERS):
        matched = page is target
        monkeypatch.setitem(
            registry._PAGE_CHECKERS,
            page,
            lambda _ctx, *, absent=False, _m=matched, **_kwargs: _m != absent,
        )
    monkeypatch.setattr(
        home,
        'check_home_news_overlay',
        lambda _ctx: SimpleNamespace(matched=False, checked=None),
    )
    monkeypatch.setattr(home, 'check_home_reward_overlay', lambda _ctx: False)
    monkeypatch.setattr(home, 'check_home_reward_confirm', lambda _ctx: False)
    # 浮窗链收尾要判断「是不是已经停在侧边栏」，替身一律当作不在，走点击那条路。
    monkeypatch.setattr(
        sidebar, 'check_sidebar_page', lambda _ctx, **_options: False
    )
    # 「首页 → 出征页」会切回出征标签。标签项是 frozen dataclass，注册时已绑定
    # checker 引用，因此整项替换而不是改模块属性；点击保留真实现（它只点击、
    # 不识别），只把 checker 换成替身；稳定等待在单测里没有意义。
    sortie_tab = registry.get_tabs(PageName.SORTIE_MAP)['sortie']
    monkeypatch.setitem(
        registry._TABS[PageName.SORTIE_MAP],
        'sortie',
        NavTab(sortie_tab.click, lambda _ctx, **_options: True, '出征'),
    )
    monkeypatch.setattr(executor_module.time, 'sleep', lambda _seconds: None)

    # 换区入口先识别中心、识别不到才退回固定落点；替身统一走兜底。
    monkeypatch.setattr(login, 'read_switch_entry_center', lambda _ctx: None)
    monkeypatch.setattr(login, 'read_enter_button_center', lambda _ctx: None)


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


def test_goto_page_clicks_and_confirms(monkeypatch: pytest.MonkeyPatch) -> None:
    """导航按路径逐步点击并确认到达。"""
    _accept_path(monkeypatch, PageName.SORTIE_MAP)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME.value)

    service.navigate_to(PageName.SORTIE_MAP)

    # 首页点出征入口，进入后再点一次「出征」标签（远征可收时页面会先停在远征）。
    assert ctx.runtime.ctrl.clicks == [
        (0.9430, 0.9069),
        sortie_constants.TAB_POSITIONS['sortie'],
    ]
    assert session.current_page() == PageName.SORTIE_MAP.value


def test_navigate_from_news_overlay_walks_popup_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    """停在每日公告上时，回主页会依次走完浮窗链。"""
    _accept_path(monkeypatch, PageName.HOME)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME_NEWS.value)

    service.navigate_to(PageName.HOME)

    assert session.current_page() == PageName.HOME.value


def test_goto_page_rejects_failed_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    """到达确认失败时抛错。

    出征页这条边声明了标签，因此到达确认由标签的 checker 负责，
    页面级确认不参与；这里让标签的 checker 判失败。
    """
    _accept_path(monkeypatch, PageName.SORTIE_MAP)
    sortie_tab = registry.get_tabs(PageName.SORTIE_MAP)['sortie']
    monkeypatch.setitem(
        registry._TABS[PageName.SORTIE_MAP],
        'sortie',
        NavTab(sortie_tab.click, lambda _ctx, **_options: False, '出征'),
    )
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME.value)

    with pytest.raises(NavigationError, match='标签切换失败'):
        service.navigate_to(PageName.SORTIE_MAP)


def test_news_edge_closes_and_ticks_checkbox(monkeypatch: pytest.MonkeyPatch) -> None:
    """公告边：未勾选时先勾上再关闭。"""
    _accept_path(monkeypatch, PageName.HOME_REWARD)
    monkeypatch.setattr(
        home,
        'check_home_news_overlay',
        lambda _ctx: SimpleNamespace(matched=True, checked=False),
    )
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME_NEWS.value)

    service.navigate_to(PageName.HOME_REWARD)

    clicks = ctx.runtime.ctrl.clicks
    assert home_constants.OVERLAY_POSITIONS['news_checkbox'] in clicks
    assert home_constants.OVERLAY_POSITIONS['news_close'] in clicks


def test_news_edge_does_nothing_without_overlay(monkeypatch: pytest.MonkeyPatch) -> None:
    """公告边：没有公告就什么都不做，不空点。"""
    _accept_path(monkeypatch, PageName.HOME_REWARD)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME_NEWS.value)

    service.navigate_to(PageName.HOME_REWARD)

    assert ctx.runtime.ctrl.clicks == []


def test_reward_edge_claims_then_confirms(monkeypatch: pytest.MonkeyPatch) -> None:
    """奖励边与确认边：有浮窗时各自点各自的位置。"""
    _accept_path(monkeypatch, PageName.HOME)
    monkeypatch.setattr(home, 'check_home_reward_overlay', lambda _ctx: True)
    monkeypatch.setattr(home, 'check_home_reward_confirm', lambda _ctx: True)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME_REWARD.value)

    service.navigate_to(PageName.HOME)

    clicks = ctx.runtime.ctrl.clicks
    assert home_constants.OVERLAY_POSITIONS['reward_claim'] in clicks
    assert home_constants.OVERLAY_POSITIONS['reward_confirm'] in clicks


def test_go_back_returns_to_previous_page(monkeypatch: pytest.MonkeyPatch) -> None:
    """回退到导航栈里的上一个页面。"""
    _accept_path(monkeypatch, PageName.HOME_NEWS)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME_NEWS.value)
    session.push_page(PageName.SORTIE_MAP.value)

    service.navigate_back()

    assert session.current_page() == PageName.HOME_NEWS.value


def test_go_back_rejects_empty_stack(monkeypatch: pytest.MonkeyPatch) -> None:
    """导航栈为空时回退抛错。"""
    service = NavigationService(_ctx(), session=SessionState())

    with pytest.raises(NavigationError, match='导航栈为空'):
        service.navigate_back()


def test_login_pages_register_arrival_checkers() -> None:
    """登录页与区服选择页的确认入口就是各自的 checker。"""
    assert registry.get_checker(PageName.LOGIN_PAGE) is login.check_login_page
    assert registry.get_checker(PageName.SERVER_SELECT) is login.check_server_select



def test_executor_skips_arrival_when_edge_does_not_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """边声明不确认时，到达确认直接跳过（浮窗链的中间步靠这个）。"""
    _accept_path(monkeypatch, PageName.HOME_REWARD)

    def _unexpected(_ctx: Any, **_kwargs: object) -> bool:
        raise AssertionError('不该调用确认入口')

    monkeypatch.setitem(registry._PAGE_CHECKERS, PageName.HOME_REWARD, _unexpected)
    ctx = _ctx()
    session = SessionState()
    session.push_page(PageName.HOME_NEWS.value)
    executor = NavigationExecutor(ctx, session)
    edge = NavTarget(
        PageName.HOME_REWARD,
        lambda *_args, **_kwargs: None,
        '测试边',
        confirm=False,
    )

    executor.walk_forward((edge,), {})

    assert session.current_page() == PageName.HOME_REWARD.value


def test_login_link_clicks_switch_entry_and_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """登录页 → 区服选择页 → 登录页 按各自落点点击。"""
    _accept_path(monkeypatch, PageName.SERVER_SELECT)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.LOGIN_PAGE.value)

    service.navigate_to(PageName.SERVER_SELECT)
    assert ctx.runtime.ctrl.clicks == [login_constants.CLICK_SWITCH_ENTRY]

    # 第二跳的目标换成了登录页，替身要跟着换；
    # OCR 定位失败时按静态映射兜底，仍要点到目标区服条目。
    _accept_path(monkeypatch, PageName.LOGIN_PAGE)
    monkeypatch.setattr(login, 'find_server_position', lambda _ctx, _name: None)
    service.navigate_to(PageName.LOGIN_PAGE, server='昆西')
    assert ctx.runtime.ctrl.clicks[-1] == login_constants.SERVER_POSITIONS[2]


def test_login_to_home_clicks_enter_game(monkeypatch: pytest.MonkeyPatch) -> None:
    """登录页 → 主页 点击进入游戏落点，落点是浮窗链的第一站。"""
    _accept_path(monkeypatch, PageName.HOME)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.LOGIN_PAGE.value)

    service.navigate_to(PageName.HOME)

    assert ctx.runtime.ctrl.clicks == [login_constants.CLICK_ENTER_GAME]

# ── 侧边栏域与页面内标签 ──────────────────────────────────────────────────────


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


def test_submenus_lead_to_pages() -> None:
    """两个二级菜单各自通到对应页面。"""
    build_path = registry.find_path(PageName.BUILD_SUBMENU, PageName.BUILD)
    intensify_path = registry.find_path(PageName.INTENSIFY_SUBMENU, PageName.INTENSIFY)

    assert len(build_path) == 1 and build_path[0].target is PageName.BUILD
    assert len(intensify_path) == 1 and intensify_path[0].target is PageName.INTENSIFY


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


def test_executor_enters_tab_with_tab_checker(monkeypatch: pytest.MonkeyPatch) -> None:
    """传了标签时，用标签的 checker 做到达确认。"""
    from autowsgr.application.ui.navigation import executor as executor_module

    monkeypatch.setattr(executor_module.time, 'sleep', lambda _seconds: None)

    clicks: list[str] = []
    checked: list[str] = []

    def fake_click(_ctx: object) -> None:
        clicks.append('click')

    def fake_checker(_ctx: object, **_: object) -> bool:
        checked.append('check')
        return True

    monkeypatch.setitem(
        registry._TABS,
        PageName.BUILD,
        {'destroy': NavTab(fake_click, fake_checker, '解体')},
    )

    executor = NavigationExecutor(object(), SessionState())
    executor._enter_tab(PageName.BUILD, 'destroy')

    assert clicks == ['click']
    assert checked == ['check']


def test_executor_rejects_unknown_tab(monkeypatch: pytest.MonkeyPatch) -> None:
    """页面没有该标签时到达确认直接失败。"""
    from autowsgr.application.ui.navigation import executor as executor_module

    monkeypatch.setattr(executor_module.time, 'sleep', lambda _seconds: None)
    executor = NavigationExecutor(object(), SessionState())

    with pytest.raises(NavigationError, match='没有标签'):
        executor._enter_tab(PageName.HOME, 'destroy')


def test_executor_reports_tab_switch_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """标签点完仍未激活时报标签切换失败。"""
    from autowsgr.application.ui.navigation import executor as executor_module

    monkeypatch.setattr(executor_module.time, 'sleep', lambda _seconds: None)
    monkeypatch.setitem(
        registry._TABS,
        PageName.BUILD,
        {
            'destroy': NavTab(
                lambda _ctx: None,
                lambda _ctx, **_: False,
                '解体',
            )
        },
    )

    executor = NavigationExecutor(object(), SessionState())

    with pytest.raises(NavigationError, match='标签切换失败'):
        executor._enter_tab(PageName.BUILD, 'destroy')

# ── 任务页 ──────────────────────────────────────────────────────────────────


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

    assert len(path) == 1 and path[0].target is PageName.MISSION


def test_mission_claim_flow_edges() -> None:
    """任务页 → 获得浮窗 → 任务页，两跳都通了。"""
    forward = registry.find_path(PageName.MISSION, PageName.MISSION_REWARD_CONFIRM)
    back = registry.find_path(PageName.MISSION_REWARD_CONFIRM, PageName.MISSION)

    assert len(forward) == 1 and forward[0].confirm is False
    assert len(back) == 1 and back[0].target is PageName.MISSION

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
        assert len(path) == 1 and path[0].target is page


def test_sub_page_cross_visit_goes_through_backyard() -> None:
    """从军阶室去浴室要经后院主页中转，两跳。"""
    path = registry.find_path(PageName.RANK_ROOM, PageName.BATH)

    assert [edge.target for edge in path] == [PageName.BACKYARD, PageName.BATH]


def test_sub_pages_return_home_through_popup_chain() -> None:
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
        assert len(back_path) == 1 and back_path[0].target is PageName.BACKYARD



