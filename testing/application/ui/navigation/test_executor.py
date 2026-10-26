"""模块功能：验证执行器的逐边执行、到达确认与页面内标签。

直接调用方：项目测试运行器。

直接依赖：pytest、navigation 的注册中心与执行器、dispatch 会话状态。

边界：用替身接管设备点击与页面确认，不连接设备、不识别画面。
"""

from __future__ import annotations

from typing import Any

import pytest

from autowsgr.application.ui.navigation import registry
from autowsgr.application.ui.navigation.executor import NavigationExecutor
from autowsgr.application.ui.navigation.types import NavigationError, NavTab, NavTarget, PageName
from autowsgr.dispatch.session import SessionState


def test_executor_skips_arrival_when_edge_does_not_confirm(
    ctx: Any, accept_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """边声明不确认时，到达确认直接跳过（浮窗链的中间步靠这个）。"""
    accept_path(PageName.HOME_REWARD)

    def _unexpected(_ctx: Any, **_kwargs: object) -> bool:
        raise AssertionError('不该调用确认入口')

    monkeypatch.setitem(registry._PAGE_CHECKERS, PageName.HOME_REWARD, _unexpected)
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
