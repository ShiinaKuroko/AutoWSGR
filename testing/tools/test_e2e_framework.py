"""E2E 生命周期的最小无设备回归。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from tools.e2e.framework import E2ERunner


def _runner() -> E2ERunner:
    runner = E2ERunner('unit', SimpleNamespace())
    ctrl = MagicMock()
    ctrl.is_app_running.return_value = False
    runner.ctx = SimpleNamespace(
        ctrl=ctrl,
        config=SimpleNamespace(
            account=SimpleNamespace(game_app=SimpleNamespace(package_name='pkg'))
        ),
    )
    runner._launcher = SimpleNamespace(ctrl=ctrl, disconnect=ctrl.disconnect)
    return runner


def test_unexpected_exit_reinitializes_once() -> None:
    runner = _runner()
    initialize = MagicMock()
    runner._initialize_game = initialize

    assert runner._ensure_game_running() is True
    initialize.assert_called_once_with()


def test_cleanup_returns_home_and_disconnects_once() -> None:
    runner = _runner()
    initialize = MagicMock()
    runner._initialize_game = initialize

    runner.cleanup()
    runner.cleanup()

    initialize.assert_called_once_with()
    runner._launcher.disconnect.assert_called_once_with()
