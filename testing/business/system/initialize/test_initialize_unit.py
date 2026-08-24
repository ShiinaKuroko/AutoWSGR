"""business.system 初始化链路的无设备单元测试。

覆盖:
- overlays.py: 日期门控（每日一次零开销）
- updater.py: 空判断（默认 needs_update 永远 False）
- initialize.py: 三分支终态（首页 / 游戏内导航 / 非游戏启动 + SL）
              重启只允许 1 次，失败即抛异常
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from autowsgr.types import PageName


_TODAY = date(2026, 8, 8)
_YESTERDAY = date(2026, 8, 7)


# ═══════════════════════════════════════════════════════════════════════════════
# overlays.py — 日期门控
# ═══════════════════════════════════════════════════════════════════════════════


class TestDailyOverlays:
    """每日弹窗处理: 保持原逻辑（0 点后第一次回首页触发）。"""

    @staticmethod
    def _make_ctrl() -> MagicMock:
        return MagicMock()

    @staticmethod
    def _freeze_today(monkeypatch: pytest.MonkeyPatch, overlays_mod) -> None:
        date_type = MagicMock()
        date_type.today.return_value = _TODAY
        monkeypatch.setattr(overlays_mod, 'date', date_type)

    def test_gate_skips_when_already_handled_today(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """当日日期匹配时，零开销直接返回，不截图。"""
        from autowsgr.business.system.initialize import overlays

        self._freeze_today(monkeypatch, overlays)
        ctrl = self._make_ctrl()
        state = SimpleNamespace(last_handled=_TODAY)

        overlays.handle_daily_overlays(ctrl, state)

        ctrl.screenshot.assert_not_called()

    def test_processes_once_on_date_change(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """日期变更后第一次调用触发清除流程；第二次零开销跳过。"""
        from autowsgr.business.system.initialize import overlays

        self._freeze_today(monkeypatch, overlays)
        ctrl = self._make_ctrl()
        detect = MagicMock(return_value=None)  # 没有浮层
        confirm = MagicMock(return_value=False)  # 没有确认弹窗
        monkeypatch.setattr(overlays, 'detect_overlay', detect)
        monkeypatch.setattr(overlays, 'confirm_operation', confirm)

        state = SimpleNamespace(last_handled=_YESTERDAY)

        # 第一次: 触发检测
        overlays.handle_daily_overlays(ctrl, state)
        detect.assert_called_once()
        assert state.last_handled == _TODAY

        # 第二次: 零开销跳过
        detect.reset_mock()
        overlays.handle_daily_overlays(ctrl, state)
        detect.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# updater.py — 更新检测空判断
# ═══════════════════════════════════════════════════════════════════════════════


class TestUpdater:
    """更新检测: 空实现占位，为后续更新处理预留接口。"""

    def test_needs_update_default_false(self) -> None:
        """默认 needs_update 永远 False — 不改变原行为。"""
        from autowsgr.business.system.initialize import updater

        assert updater.needs_update(MagicMock()) is False

    def test_handle_is_noop(self) -> None:
        """handle 调用不抛异常，不做任何动作。"""
        from autowsgr.business.system.initialize import updater

        ctrl = MagicMock()
        updater.handle(ctrl)
        ctrl.click.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# initialize.py — 三分支终态 + SL 上限
# ═══════════════════════════════════════════════════════════════════════════════


def _make_ctx() -> SimpleNamespace:
    """构造 initialize 所需的最小上下文。"""
    ctrl = MagicMock()
    ctrl.is_app_running.return_value = True
    return SimpleNamespace(
        ctrl=ctrl,
        config=SimpleNamespace(account=SimpleNamespace(game_app='官服')),
    )


class TestInitialize:
    """初始化三分支判定 + 启动画面点击 + 重启只试 1 次 + 首页验证。"""

    # ── 分支 1: 已在首页 → 清浮层 → 完成 ─────────────────────────────────

    def test_already_on_main_just_dismisses_overlays(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """游戏在运行且已经在首页：只处理浮层，不启动不导航。"""
        from autowsgr.business.system.initialize import initialize, overlays

        ctx = _make_ctx()
        monkeypatch.setattr(
            initialize, 'identify_current_page', lambda _c, **_k: PageName.MAIN
        )
        dismiss = MagicMock()
        monkeypatch.setattr(overlays, 'handle_daily_overlays', dismiss)

        initialize.initialize(ctx)

        ctx.ctrl.start_app.assert_not_called()
        dismiss.assert_called_once()

    # ── 分支 2: 游戏内但不在首页 → 导航回首页 ─────────────────────────────

    def test_known_non_main_page_navigates_home(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """页面认识但不是首页：调用 goto_page 导航，成功后清浮层。"""
        from autowsgr.business.system.initialize import initialize, overlays

        ctx = _make_ctx()
        goto_page = MagicMock()
        monkeypatch.setattr(initialize, 'goto_page', goto_page)
        dismiss = MagicMock()
        monkeypatch.setattr(overlays, 'handle_daily_overlays', dismiss)
        monkeypatch.setattr(
            initialize, 'identify_current_page', lambda _c, **_k: PageName.MAP
        )

        initialize.initialize(ctx)

        goto_page.assert_called_once_with(ctx, PageName.MAIN)
        dismiss.assert_called_once()

    # ── 分支 3: 游戏未运行 → 启动 → 验证首页 ─────────────────────────────

    def test_game_stopped_starts_app_and_verifies_main(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """游戏未运行：启动 App → 检测启动画面 → 点进入 → 浮层 → 终态在首页。"""
        from autowsgr.business.system.initialize import initialize, overlays

        ctx = _make_ctx()
        ctx.ctrl.is_app_running.return_value = False
        start = MagicMock()
        monkeypatch.setattr(initialize, '_start_game_flow', start)
        monkeypatch.setattr(
            initialize, 'identify_current_page', lambda _c, **_k: PageName.MAIN
        )
        dismiss = MagicMock()
        monkeypatch.setattr(overlays, 'handle_daily_overlays', dismiss)

        initialize.initialize(ctx)

        start.assert_called_once()
        dismiss.assert_called_once()

    # ── SL 边界: 重启只试 1 次 ──────────────────────────────────────────

    def test_restart_limit_prevents_infinite_loop(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """页面识别不出 + 导航失败 → SL 重启一次；仍失败 → 抛异常。"""
        from autowsgr.business.system.initialize import initialize
        from autowsgr.ui.utils import NavigationError

        ctx = _make_ctx()

        restart = MagicMock()
        monkeypatch.setattr(initialize, '_restart_game', restart)
        # 识别: 全程 None (页面不认识)
        monkeypatch.setattr(
            initialize, 'identify_current_page', lambda _c, **_k: None
        )
        # goto_page 每次都失败 (导航超时)
        def _nav_fail(_c, _t):
            raise NavigationError('timeout')

        monkeypatch.setattr(initialize, 'goto_page', _nav_fail)

        # 假时钟: sleep 推进单调时钟, 避免真实等待 20s 恢复超时
        clock = {'now': 100.0}
        monkeypatch.setattr(initialize.time, 'monotonic', lambda: clock['now'])
        monkeypatch.setattr(
            initialize.time, 'sleep', lambda s: clock.__setitem__('now', clock['now'] + s)
        )

        with pytest.raises(RuntimeError, match='初始化失败'):
            initialize.initialize(ctx)

        assert restart.call_count == 1, '只允许重启 1 次防止死循环'

    # ── 启动流程中调用 updater 空判断 ─────────────────────────────────────

    def test_updater_called_in_start_flow(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """启动过程中会做一次更新检测空判断 (未来扩展点)。"""
        from autowsgr.business.system.initialize import initialize, overlays, updater

        ctx = _make_ctx()
        ctx.ctrl.is_app_running.return_value = False

        needs_update = MagicMock(return_value=False)
        handle = MagicMock()
        monkeypatch.setattr(updater, 'needs_update', needs_update)
        monkeypatch.setattr(updater, 'handle', handle)

        # 让 _start_game_flow 跑最小路径: 启动画面命中 → 点进入 → 完成
        monkeypatch.setattr(initialize, '_wait_for_start_screen', lambda _c: True)
        monkeypatch.setattr(initialize, '_click_enter', lambda _c: None)
        monkeypatch.setattr(initialize, '_is_on_main_page', lambda _c: True)
        monkeypatch.setattr(
            initialize, 'identify_current_page', lambda _c, **_k: PageName.MAIN
        )
        monkeypatch.setattr(overlays, 'handle_daily_overlays', MagicMock())

        initialize.initialize(ctx)

        # 启动画面等待后会做一次 needs_update 判断
        needs_update.assert_called_once()
