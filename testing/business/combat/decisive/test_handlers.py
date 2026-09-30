"""决战地图进入后的浮层稳定等待测试。

上层调用：
- pytest：验证进入地图后首帧识别不会抢在浮层动画完成前执行。

下层依赖：
- business.combat.decisive.handlers：提供进入地图状态处理器。
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from autowsgr.application.errors import ManualRepairRequiredError
from autowsgr.business.combat import CombatResult
from autowsgr.business.combat.decisive import handlers
from autowsgr.common.types import (
    ConditionFlag,
    DecisiveEntryStatus,
    DecisivePhase,
    FleetSelection,
    Formation,
)


def test_enter_map_starts_recognition_window_without_blind_delay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """进入地图后交给正向阶段识别，不执行固定的盲等待。"""
    events: list[object] = []
    battle_page = MagicMock()
    battle_page.read_entry_status.return_value = DecisiveEntryStatus.CHALLENGING
    battle_page.read_stage.return_value = 1
    battle_page.click_enter_map.side_effect = lambda: events.append('enter')
    context = SimpleNamespace(
        _battle_page=battle_page,
        _config=SimpleNamespace(chapter=6),
        _ctrl=MagicMock(),
        _state=SimpleNamespace(stage=None, phase=None),
        _use_last_fleet_attempts=1,
        _wait_deadline=None,
        _resume_mode=True,
        _fleet_overlay_enabled=True,
        _force_fleet_scan=False,
        _full_recovery_check=False,
        _skip_advance_choice=False,
        _advance_source_node=None,
    )
    monkeypatch.setattr(handlers.time, 'monotonic', lambda: 100.0)
    monkeypatch.setattr(handlers.time, 'sleep', lambda delay: events.append(('sleep', delay)))

    handlers.DecisivePhaseHandlers._handle_enter_map(context)

    assert events == ['enter']
    assert context._state.stage == 1
    assert context._state.phase is DecisivePhase.WAITING_FOR_MAP
    assert context._wait_deadline == 115.0


def test_advance_choice_returns_to_waiting_for_fresh_phase_recognition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected: list[object] = []
    context = SimpleNamespace(
        _logic=SimpleNamespace(get_advance_choice=lambda _options: 0),
        _map=SimpleNamespace(
            select_advance_card=lambda index, **kwargs: selected.append((index, kwargs)),
        ),
        _state=SimpleNamespace(phase=DecisivePhase.ADVANCE_CHOICE),
        _advance_choice_roi=lambda: None,
        _advance_source_node='B',
        _wait_deadline=0.0,
        _skip_advance_choice=False,
    )
    monkeypatch.setattr(handlers.time, 'monotonic', lambda: 100.0)

    handlers.DecisivePhaseHandlers._handle_advance_choice(context)

    assert selected == [(0, {'advance_choice_roi': None})]
    assert context._state.phase is DecisivePhase.WAITING_FOR_MAP
    assert context._advance_source_node is None
    assert context._skip_advance_choice is True
    assert context._wait_deadline == 110.0


def test_prepare_combat_passes_current_overlay_policy_to_phase_reader() -> None:
    screen = object()
    route_roi = object()
    read_phase = MagicMock(return_value=DecisivePhase.CHOOSE_FLEET)
    context = SimpleNamespace(
        _ctrl=SimpleNamespace(screenshot=lambda: screen),
        _map=SimpleNamespace(read_decisive_phase=read_phase),
        _advance_choice_roi=lambda: route_roi,
        _fleet_overlay_enabled=False,
        _state=SimpleNamespace(phase=DecisivePhase.PREPARE_COMBAT),
    )

    handlers.DecisivePhaseHandlers._handle_prepare_combat(context)

    read_phase.assert_called_once_with(
        screen,
        advance_choice_roi=route_roi,
        allow_fleet_overlay=False,
    )
    assert context._state.phase is DecisivePhase.CHOOSE_FLEET


def test_choose_fleet_does_not_buy_after_overlay_disappears() -> None:
    selection = FleetSelection('unconfigured', 1, (0.25, 0.5))
    recognize = MagicMock(
        side_effect=[
            (object(), 10, {'unconfigured': selection}),
            (object(), 10, {'unconfigured': selection}),
        ]
    )
    buy = MagicMock()
    context = SimpleNamespace(
        _recognize_fleet_options_with_retry=recognize,
        _state=SimpleNamespace(
            score=10,
            ships=set(),
            is_begin=lambda: False,
            phase=DecisivePhase.CHOOSE_FLEET,
        ),
        _logic=SimpleNamespace(choose_ships=lambda *_args, **_kwargs: []),
        _map=SimpleNamespace(
            refresh_fleet=MagicMock(),
            close_fleet_overlay=MagicMock(return_value=False),
            check_fleet_overlay_open=MagicMock(return_value=False),
            buy_fleet_option=buy,
        ),
    )

    with pytest.raises(RuntimeError, match='拒绝点击兜底舰船'):
        handlers.DecisivePhaseHandlers._handle_choose_fleet(context)

    buy.assert_not_called()


def test_manual_repair_terminates_decisive_task_after_bath_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = MagicMock()
    page.check_repair.return_value = [0]
    context = SimpleNamespace(
        _ctx=object(),
        _ctrl=SimpleNamespace(screenshot=MagicMock(return_value=object())),
        _map=SimpleNamespace(
            read_decisive_phase=lambda *_args, **_kwargs: None,
            enter_formation=MagicMock(),
            check_skill_used=lambda: True,
        ),
        _advance_choice_roi=lambda: None,
        _fleet_overlay_enabled=False,
        _full_recovery_check=False,
        _force_fleet_scan=False,
        _resume_mode=False,
        _has_chosen_fleet=True,
        _state=SimpleNamespace(
            node='B',
            stage=1,
            ships={'target-ship'},
            fleet=['', 'target-ship', '', '', '', '', ''],
            ship_stats=[],
            phase=DecisivePhase.PREPARE_COMBAT,
            is_begin=lambda: False,
        ),
        _logic=SimpleNamespace(
            get_best_fleet=lambda: ['', 'target-ship', '', '', '', '', ''],
            should_retreat=lambda _fleet: False,
        ),
        _config=SimpleNamespace(use_quick_repair=False, repair_level=1),
    )
    route = MagicMock()
    repair = MagicMock()
    monkeypatch.setattr(handlers, 'BattlePreparationPage', lambda _ctx: page)
    monkeypatch.setattr(handlers, 'goto_bath_from_decisive_sortie', route)
    monkeypatch.setattr(handlers, 'repair_manual_targets_in_bath', repair)
    monkeypatch.setattr(handlers.time, 'sleep', lambda _delay: None)

    with pytest.raises(ManualRepairRequiredError, match='需要手动修理'):
        handlers.DecisivePhaseHandlers._handle_prepare_combat(context)

    route.assert_called_once_with(context._ctx)
    repair.assert_called_once_with(context._ctx, ['target-ship'])
    page.try_start_battle.assert_not_called()


def test_non_success_decisive_combat_does_not_advance_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = SimpleNamespace(
        stage=1,
        node='B',
        ship_stats=[],
        phase=DecisivePhase.IN_COMBAT,
    )
    context = SimpleNamespace(
        _state=state,
        _logic=SimpleNamespace(
            get_formation=lambda: Formation.double_column,
            is_key_point=lambda: False,
        ),
        _ctx=SimpleNamespace(
            ctrl=object(),
            ocr=None,
            stop_event=SimpleNamespace(is_set=lambda: False),
        ),
        _ctrl=object(),
        _sync_ship_states=lambda: None,
    )
    monkeypatch.setattr(
        handlers,
        'run_combat',
        lambda *_args, **_kwargs: CombatResult(flag=ConditionFlag.SL),
    )

    with pytest.raises(RuntimeError, match='未成功'):
        handlers.DecisivePhaseHandlers._handle_combat(context)

    assert state.phase is DecisivePhase.IN_COMBAT
