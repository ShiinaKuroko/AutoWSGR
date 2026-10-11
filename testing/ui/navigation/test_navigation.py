"""模块功能：验证导航器的路径拼接、确认与回退。

直接调用方：项目测试运行器。

直接依赖：pytest、navigation 的注册中心与入口、dispatch 会话状态。

边界：用替身接管设备点击与页面确认，不连接设备、不识别画面。
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from typing import Any

import pytest

from autowsgr.application.ui.controller.home.main_page import constants as home_constants
from autowsgr.application.ui.controller.login import constants as login_constants
from autowsgr.application.ui.navigation import registry
from autowsgr.application.ui.navigation.executor import NavigationExecutor
from autowsgr.application.ui.navigation.page_checker import home_checker, login_checker
from autowsgr.application.ui.navigation.service import NavigationService
from autowsgr.application.ui.navigation.types import NavigationError, NavTarget, PageName
from autowsgr.dispatch.session import SessionState


class _Ctrl:
    """设备服务替身，记录点击落点。"""

    def __init__(self) -> None:
        self.clicks: list[tuple[float, float]] = []

    def click(self, x: float, y: float, *, delay: bool = False) -> None:  # noqa: ARG002
        self.clicks.append((x, y))


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """每日浮窗流程里的等待对测试没有意义，直接跳过。"""
    monkeypatch.setattr(time, 'sleep', lambda _seconds: None)


def _ctx() -> Any:
    """构造带活动任务参数的上下文替身。"""
    return SimpleNamespace(
        runtime=SimpleNamespace(ctrl=_Ctrl()),
        read_event_type=lambda: 'stage_push',
        read_event_stage=lambda: 'EX7',
    )


def _accept_all(monkeypatch: pytest.MonkeyPatch) -> None:
    """让所有已注册页面的确认入口都返回真，并让每日浮窗视为不存在。

    替身不区分前后识别：前识别返回真（页面在），后识别也返回真（已离开），
    这样用例只验证「点击 + 到达确认」，离开确认自己的失败路径另有专门用例。
    """
    for page in list(registry._PAGE_CHECKERS):
        monkeypatch.setitem(registry._PAGE_CHECKERS, page, lambda _ctx, **_kwargs: True)
    monkeypatch.setattr(
        home_checker,
        'check_home_news_overlay',
        lambda _ctx: SimpleNamespace(matched=False, checked=None),
    )
    monkeypatch.setattr(home_checker, 'check_home_reward_overlay', lambda _ctx: False)
    # 换区入口先识别中心、识别不到才退回固定落点；替身统一走兜底。
    monkeypatch.setattr(login_checker, 'read_switch_entry_center', lambda _ctx: None)
    monkeypatch.setattr(login_checker, 'read_enter_button_center', lambda _ctx: None)


def test_find_path_multi_hop() -> None:
    """多跳路径按广度拼接。"""
    path = registry.find_path(PageName.SORTIE_MAP, PageName.EVENT_MAP)

    assert [edge.target for edge in path] == [PageName.HOME, PageName.EVENT_MAP]


def test_find_path_same_page() -> None:
    """起点即目标时返回空路径。"""
    assert registry.find_path(PageName.HOME, PageName.HOME) == ()


def test_find_path_rejects_unreachable() -> None:
    """没有可达路径时抛错。"""
    with pytest.raises(NavigationError, match='没有从'):
        registry.find_path(PageName.HOME, PageName.BATH)


def test_goto_page_clicks_and_confirms(monkeypatch: pytest.MonkeyPatch) -> None:
    """导航按路径逐步点击并确认到达。"""
    _accept_all(monkeypatch)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME.value)

    service.navigate_to(PageName.SORTIE_MAP)

    assert ctx.runtime.ctrl.clicks == [(0.9430, 0.9069)]
    assert session.current_page() == PageName.SORTIE_MAP.value


def test_goto_page_runs_daily_popup_when_passing_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """经过首页时先跑一次每日弹窗前置流程。"""
    _accept_all(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(NavigationService, '_handle_daily_news', lambda _self: calls.append('news'))
    monkeypatch.setattr(
        NavigationService,
        '_handle_daily_reward',
        lambda _self: calls.append('reward'),
    )
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME.value)

    service.navigate_to(PageName.SORTIE_MAP)

    assert calls == ['news', 'reward']
    assert session.daily_popup_handled is True


def test_goto_page_skips_daily_popup_after_handled(monkeypatch: pytest.MonkeyPatch) -> None:
    """本次运行已处理过时不再重复前置流程。"""
    _accept_all(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(NavigationService, '_handle_daily_news', lambda _self: calls.append('news'))
    monkeypatch.setattr(
        NavigationService,
        '_handle_daily_reward',
        lambda _self: calls.append('reward'),
    )
    ctx = _ctx()
    session = SessionState()
    session.mark_daily_popup_handled()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME.value)

    service.navigate_to(PageName.SORTIE_MAP)

    assert calls == []


def test_goto_page_rejects_failed_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    """到达确认失败时抛错。"""
    _accept_all(monkeypatch)
    monkeypatch.setitem(registry._PAGE_CHECKERS, PageName.SORTIE_MAP, lambda _ctx: False)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME.value)

    with pytest.raises(NavigationError, match='到达确认失败'):
        service.navigate_to(PageName.SORTIE_MAP)


def test_daily_news_clicks_checkbox_then_close(monkeypatch: pytest.MonkeyPatch) -> None:
    """公告存在且未勾选时，先点勾选框再点关闭。"""
    _accept_all(monkeypatch)
    states = iter(
        [
            SimpleNamespace(matched=True, checked=False),
            SimpleNamespace(matched=False, checked=None),
        ]
    )
    monkeypatch.setattr(
        home_checker,
        'check_home_news_overlay',
        lambda _ctx: next(states, SimpleNamespace(matched=False, checked=None)),
    )
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME.value)

    service.navigate_to(PageName.SORTIE_MAP)

    clicks = ctx.runtime.ctrl.clicks
    assert home_constants.OVERLAY_POSITIONS['news_checkbox'] in clicks
    assert home_constants.OVERLAY_POSITIONS['news_close'] in clicks


def test_daily_reward_claims_then_confirms(monkeypatch: pytest.MonkeyPatch) -> None:
    """奖励浮窗存在时领取并确认。"""
    _accept_all(monkeypatch)
    overlays = iter([True, False])
    monkeypatch.setattr(
        home_checker, 'check_home_reward_overlay', lambda _ctx: next(overlays, False)
    )
    confirms = iter([True, False])
    monkeypatch.setattr(
        home_checker, 'check_home_reward_confirm', lambda _ctx: next(confirms, False)
    )
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME.value)

    service.navigate_to(PageName.SORTIE_MAP)

    clicks = ctx.runtime.ctrl.clicks
    assert home_constants.OVERLAY_POSITIONS['reward_claim'] in clicks
    assert home_constants.OVERLAY_POSITIONS['reward_confirm'] in clicks


def test_go_back_returns_to_previous_page(monkeypatch: pytest.MonkeyPatch) -> None:
    """回退到导航栈里的上一个页面。"""
    _accept_all(monkeypatch)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.HOME.value)
    session.push_page(PageName.SORTIE_MAP.value)

    service.navigate_back()

    assert session.current_page() == PageName.HOME.value


def test_go_back_rejects_empty_stack(monkeypatch: pytest.MonkeyPatch) -> None:
    """导航栈为空时回退抛错。"""
    _accept_all(monkeypatch)
    service = NavigationService(_ctx(), session=SessionState())

    with pytest.raises(NavigationError, match='导航栈为空'):
        service.navigate_back()


def test_login_pages_register_arrival_checkers() -> None:
    """登录页与区服选择页都注册了到达确认入口，并转发到对应 checker。"""
    ctx = _ctx()
    calls: list[str] = []

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        login_checker,
        'check_login_page',
        lambda _ctx, **_kwargs: calls.append('login') or True,
    )
    monkeypatch.setattr(
        login_checker,
        'check_server_select',
        lambda _ctx, **_kwargs: calls.append('server') or True,
    )
    try:
        assert registry.get_checker(PageName.LOGIN_PAGE) is not None
        assert registry.get_checker(PageName.SERVER_SELECT) is not None
        assert registry.get_checker(PageName.LOGIN_PAGE)(ctx) is True  # type: ignore[misc]
        assert registry.get_checker(PageName.SERVER_SELECT)(ctx) is True  # type: ignore[misc]
    finally:
        monkeypatch.undo()

    assert calls == ['login', 'server']


def test_executor_rejects_failed_departure(monkeypatch: pytest.MonkeyPatch) -> None:
    """旧页标志一直不消失时，执行器抛离开确认失败。"""
    # 只注册一个永远为真的确认入口：离开确认必然轮询到底仍"存在"。
    monkeypatch.setitem(
        registry._PAGE_CHECKERS,
        PageName.SORTIE_MAP,
        lambda _ctx, *, absent=False, **_kwargs: not absent,
    )
    ctx = _ctx()
    session = SessionState()
    session.push_page(PageName.SORTIE_MAP.value)
    executor = NavigationExecutor(ctx, session)
    edge = NavTarget(PageName.HOME, lambda *_args, **_kwargs: None, '测试边')

    with pytest.raises(NavigationError, match='离开确认失败'):
        executor.walk_forward((edge,), {})


def test_login_link_clicks_switch_entry_and_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """登录页 → 区服选择页 → 登录页 按各自落点点击。"""
    _accept_all(monkeypatch)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.LOGIN_PAGE.value)

    service.navigate_to(PageName.SERVER_SELECT)
    assert ctx.runtime.ctrl.clicks == [login_constants.CLICK_SWITCH_ENTRY]

    service.navigate_to(PageName.LOGIN_PAGE, position=2)
    assert ctx.runtime.ctrl.clicks[-1] == login_constants.SERVER_POSITIONS[2]


def test_login_to_home_clicks_enter_game(monkeypatch: pytest.MonkeyPatch) -> None:
    """登录页 → 主页 点击进入游戏落点。"""
    _accept_all(monkeypatch)
    ctx = _ctx()
    session = SessionState()
    service = NavigationService(ctx, session=session)
    session.push_page(PageName.LOGIN_PAGE.value)

    service.navigate_to(PageName.HOME)

    assert ctx.runtime.ctrl.clicks == [login_constants.CLICK_ENTER_GAME]
