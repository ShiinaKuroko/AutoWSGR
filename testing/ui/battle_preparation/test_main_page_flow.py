from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from autowsgr.application.ui.controller.fleet import (
    BattlePreparationPage,
    FleetSnapshot,
    RepairStrategy,
)


def test_prepare_and_start_battle_runs_the_main_page_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    ctrl = MagicMock()
    ctx = SimpleNamespace(
        ctrl=ctrl,
        config=SimpleNamespace(repair_manually=False),
        ocr=MagicMock(),
    )
    page = BattlePreparationPage(ctx)
    events = []
    initial_snapshot = FleetSnapshot(
        names=['U-47', None, None, None, None, None],
        occupied=[True, False, False, False, False, False],
    )
    final_snapshot = FleetSnapshot(
        names=['U-47', 'U-96', None, None, None, None],
        occupied=[True, True, False, False, False, False],
    )

    monkeypatch.setattr(page, 'check_current_page', lambda _screen: events.append('check') or True)
    monkeypatch.setattr(
        page,
        'adjust_fleet',
        lambda **kwargs: events.append(('adjust', kwargs)) or initial_snapshot,
    )
    monkeypatch.setattr(page, 'apply_supply', lambda: events.append('supply'))
    monkeypatch.setattr(
        page,
        'apply_repair',
        lambda strategy, **kwargs: events.append(('repair', strategy, kwargs)),
    )
    monkeypatch.setattr(
        page,
        'read_fleet_snapshot',
        lambda **kwargs: events.append(('read', kwargs)) or final_snapshot,
    )
    monkeypatch.setattr(
        page,
        'try_start_battle',
        lambda **kwargs: events.append(('start', kwargs['target'])) or True,
    )

    result = page.prepare_and_start_battle(
        fleet_id=2,
        fleet_rules=['U-47'],
        task_type='campaign',
        repair_strategy=RepairStrategy.MODERATE,
        target='campaign combat',
    )

    assert result is final_snapshot
    assert events == [
        'check',
        (
            'adjust',
            {
                'fleet_id': 2,
                'fleet_rules': ['U-47'],
                'task_type': 'campaign',
                'recognize_ship_types': True,
            },
        ),
        'supply',
        ('repair', RepairStrategy.MODERATE, {'repair_manually': None}),
        ('read', {'recognize_ship_types': True}),
        ('start', 'campaign combat'),
    ]
