"""模块功能：验证执行器的逐边执行、到达确认与页面内标签。

直接调用方：项目测试运行器。

直接依赖：pytest、navigation 的注册中心与执行器、dispatch 会话状态。

边界：用替身接管设备点击与页面确认，不连接设备、不识别画面。
"""

from __future__ import annotations

from typing import Any

import pytest

from autowsgr.application.signals import TaskPaused
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


# ── 到达确认 ────────────────────────────────────────────────────────────────


def test_executor_confirms_domain_arrival_with_probes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """域页面到达确认只问域探针，不扫全层。"""
    from autowsgr.application.ui.navigation import executor as executor_module

    slept: list[float] = []
    arrivals: list[PageName] = []
    monkeypatch.setattr(executor_module.time, 'sleep', slept.append)
    monkeypatch.setattr(registry, 'is_domain_page', lambda _page: True)
    monkeypatch.setattr(registry, 'on_arrival', lambda _ctx, page: arrivals.append(page))
    monkeypatch.setattr(
        registry,
        'probe_domains',
        lambda _ctx, **_options: (PageName.SORTIE_MAP,),
    )

    executor = NavigationExecutor(object(), SessionState())
    monkeypatch.setattr(
        executor,
        'detect_layer',
        lambda **_options: pytest.fail('域到达确认不该扫全层'),
    )

    edge = NavTarget(PageName.SORTIE_MAP, lambda *_args, **_kwargs: None, '首页 → 出征页')
    executor._confirm_arrival(edge)

    assert slept == [executor_module._DOMAIN_ARRIVAL_SETTLE_SECONDS]
    assert arrivals == [PageName.SORTIE_MAP]


def test_executor_reports_domain_arrival_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """域探针没认出目标页时报到达确认失败。"""
    from autowsgr.application.ui.navigation import executor as executor_module

    monkeypatch.setattr(executor_module.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(registry, 'is_domain_page', lambda _page: True)
    monkeypatch.setattr(
        registry,
        'probe_domains',
        lambda _ctx, **_options: (PageName.EXERCISE,),
    )

    executor = NavigationExecutor(object(), SessionState())
    edge = NavTarget(PageName.SORTIE_MAP, lambda *_args, **_kwargs: None, '首页 → 出征页')

    with pytest.raises(NavigationError, match='未识别到'):
        executor._confirm_arrival(edge)


# ── 任务页 ──────────────────────────────────────────────────────────────────


# ── 断点 ────────────────────────────────────────────────────────────────────


class _CheckpointRecorder:
    """记录断点调用次数的上下文替身。"""

    def __init__(self) -> None:
        self.calls = 0

    def check_interrupt(self) -> None:
        self.calls += 1


def _two_edges() -> tuple[NavTarget, NavTarget]:
    """两条都不做到达确认的边，避开真实识别。"""
    return (
        NavTarget(PageName.HOME_REWARD, lambda *_args, **_kwargs: None, '甲', confirm=False),
        NavTarget(
            PageName.HOME_REWARD_CONFIRM, lambda *_args, **_kwargs: None, '乙', confirm=False
        ),
    )


def test_executor_checks_interrupt_at_entry_and_after_each_forward_edge() -> None:
    """前进在入口与每条边压栈之后各查一次断点。"""
    recorder = _CheckpointRecorder()
    session = SessionState()
    session.push_page(PageName.HOME.value)

    NavigationExecutor(recorder, session).walk_forward(_two_edges(), {})

    assert recorder.calls == 3
    assert session.current_page() == PageName.HOME_REWARD_CONFIRM.value


def test_executor_checks_interrupt_after_each_backward_edge() -> None:
    """后退在每条边确认到达之后查断点。"""
    recorder = _CheckpointRecorder()

    NavigationExecutor(recorder, SessionState()).walk_backward(_two_edges())

    assert recorder.calls == 2


def test_executor_skips_interrupt_when_checkpoint_disabled() -> None:
    """终止收尾那一趟关掉断点，否则停止开关还亮着会立刻再抛一次。"""
    recorder = _CheckpointRecorder()

    NavigationExecutor(recorder, SessionState(), checkpoint=False).walk_forward(
        (_two_edges()[0],), {}
    )

    assert recorder.calls == 0


def test_executor_leaves_complete_backtrack_after_interrupt() -> None:
    """断点抛出时栈已经记到刚才那一跳，让路不丢回退路径。"""

    class _StopOnSecondCheck(_CheckpointRecorder):
        def check_interrupt(self) -> None:
            self.calls += 1
            if self.calls == 2:
                raise TaskPaused

    recorder = _StopOnSecondCheck()
    session = SessionState()
    session.push_page(PageName.HOME.value)

    with pytest.raises(TaskPaused):
        NavigationExecutor(recorder, session).walk_forward(_two_edges(), {})

    assert session.current_page() == PageName.HOME_REWARD.value
