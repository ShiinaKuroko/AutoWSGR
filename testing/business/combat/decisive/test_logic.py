from __future__ import annotations

from types import SimpleNamespace

from autowsgr.business.combat.decisive.logic import DecisiveLogic
from autowsgr.common.types import FleetSelection


def test_choose_ships_uses_level2_when_no_level1_is_available() -> None:
    config = SimpleNamespace(level1=['Primary'], level2=['Backup'])
    state = SimpleNamespace(fleet=[''] * 7, score=10)
    logic = DecisiveLogic(config, state)

    assert logic.choose_ships(
        {'Backup': FleetSelection('Backup', 4, (0.25, 0.5))},
        first_node=False,
    ) == ['Backup']


def test_choose_ships_prioritizes_level1_before_level2() -> None:
    config = SimpleNamespace(level1=['Primary'], level2=['Backup'])
    state = SimpleNamespace(fleet=[''] * 7, score=10)
    logic = DecisiveLogic(config, state)

    assert logic.choose_ships(
        {
            'Primary': FleetSelection('Primary', 4, (0.25, 0.5)),
            'Backup': FleetSelection('Backup', 4, (0.375, 0.5)),
        },
        first_node=False,
    ) == ['Primary', 'Backup']


def test_choose_ships_first_node_preserves_two_ship_goal() -> None:
    config = SimpleNamespace(level1=['Primary'], level2=['BackupA', 'BackupB'])
    state = SimpleNamespace(fleet=[''] * 7, ships=set(), score=10)
    logic = DecisiveLogic(config, state)

    assert logic.choose_ships(
        {
            'Primary': FleetSelection('Primary', 6, (0.25, 0.5)),
            'BackupA': FleetSelection('BackupA', 5, (0.375, 0.5)),
            'BackupB': FleetSelection('BackupB', 5, (0.5, 0.5)),
        },
        first_node=True,
    ) == ['BackupA', 'BackupB']


def test_choose_ships_fills_pool_before_primary_upgrade() -> None:
    config = SimpleNamespace(level1=['Primary'], level2=['BackupA', 'BackupB'])
    state = SimpleNamespace(
        fleet=[''] * 7,
        ships={'BackupA', 'OwnedA', 'OwnedB', 'OwnedC'},
        score=10,
    )
    logic = DecisiveLogic(config, state)

    assert logic.choose_ships(
        {
            'Primary': FleetSelection('Primary', 6, (0.25, 0.5)),
            'BackupB': FleetSelection('BackupB', 4, (0.375, 0.5)),
            'BackupA': FleetSelection('BackupA', 4, (0.5, 0.5)),
        },
        first_node=False,
    ) == ['Primary', 'BackupB']


def test_choose_ships_upgrades_existing_primary_only() -> None:
    config = SimpleNamespace(level1=['Primary'], level2=['Backup'])
    state = SimpleNamespace(
        fleet=[''] * 7,
        ships={'Primary', 'Backup', 'Ship3', 'Ship4', 'Ship5', 'Ship6'},
        score=10,
    )
    logic = DecisiveLogic(config, state)

    assert logic.choose_ships(
        {
            'Primary': FleetSelection('Primary', 4, (0.25, 0.5)),
            'Backup': FleetSelection('Backup', 1, (0.375, 0.5)),
        },
        first_node=False,
    ) == ['Primary']


def test_best_fleet_keeps_current_unavailable_ship() -> None:
    config = SimpleNamespace(level1=['Primary'], level2=['Backup'], flagship_priority=[])
    state = SimpleNamespace(
        fleet=['', 'Primary', 'Backup', '', '', '', ''],
        ships={'Primary', 'Backup'},
    )
    ctx = SimpleNamespace(is_ship_available=lambda name: name != 'Primary')
    logic = DecisiveLogic(config, state, ctx=ctx)

    assert logic.get_best_fleet() == ['', 'Primary', 'Backup', '', '', '', '']
