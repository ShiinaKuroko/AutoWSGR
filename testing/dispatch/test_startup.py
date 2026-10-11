"""模块功能：验证启动编排入口的三条路径。

直接调用方：项目测试运行器。

直接依赖：pytest、dispatch.startup 与导航器错误类型。

边界：用导航器替身接管启动与导航，不连接设备、不识别画面。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from autowsgr.application.errors import ManualRepairRequiredError
from autowsgr.application.ui.navigation.types import (
    ManualUpdateRequiredError,
    NavigationError,
    PageName,
)
from autowsgr.dispatch import startup


def _ctx(*, running: bool) -> Any:
    """构造带设备与配置替身的上下文。"""
    ctrl = SimpleNamespace(
        check_app_running=lambda _package: running,
        follow_display=lambda _package: None,
    )
    account = SimpleNamespace(package_name='com.example.game')
    runtime = SimpleNamespace(ctrl=ctrl, config=SimpleNamespace(account=account))
    return SimpleNamespace(runtime=runtime)


def _install_navigator(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[str],
    *,
    navigate_error: Exception | None = None,
) -> None:
    """用导航器替身接管启动与导航；导航错误只抛第一次。"""
    raised = {'done': False}

    class _Navigator:
        def __init__(self, _ctx: Any) -> None:
            pass

        def ensure_started(self) -> None:
            calls.append('ensure_started')

        def ensure_server_selected(self) -> None:
            calls.append('ensure_server_selected')

        def navigate_to(self, target: PageName, **_params: object) -> None:
            calls.append(target.value)
            if navigate_error is not None and not raised['done']:
                raised['done'] = True
                raise navigate_error

        def restart_game(self) -> None:
            calls.append('restart_game')

    monkeypatch.setattr(startup, 'NavigationService', _Navigator)


def test_starts_game_when_not_running(monkeypatch: pytest.MonkeyPatch) -> None:
    """游戏没运行时先走启动流程，再回主页。"""
    calls: list[str] = []
    _install_navigator(monkeypatch, calls)

    startup.ensure_ready(_ctx(running=False))

    assert calls == ['ensure_started', PageName.HOME.value]


def test_skips_start_when_game_already_running(monkeypatch: pytest.MonkeyPatch) -> None:
    """游戏在运行时只走导航，不重复启动。"""
    calls: list[str] = []
    _install_navigator(monkeypatch, calls)

    startup.ensure_ready(_ctx(running=True))

    assert calls == ['ensure_server_selected', PageName.HOME.value]


def test_update_required_becomes_manual_repair_without_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """需要更新时转成人工处理错误，且不触发 SL。"""
    calls: list[str] = []
    _install_navigator(monkeypatch, calls, navigate_error=ManualUpdateRequiredError('需要更新'))

    with pytest.raises(ManualRepairRequiredError, match='手动完成'):
        startup.ensure_ready(_ctx(running=True))

    assert calls == ['ensure_server_selected', PageName.HOME.value]


def test_navigation_failure_restarts_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """导航失败时 SL 一次并重试导航。"""
    calls: list[str] = []
    _install_navigator(monkeypatch, calls, navigate_error=NavigationError('识别不到页面'))

    startup.ensure_ready(_ctx(running=True))

    assert calls == [
        'ensure_server_selected',
        PageName.HOME.value,
        'restart_game',
        PageName.HOME.value,
    ]
