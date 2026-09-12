"""决战编队入口的页面路由回归。"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from autowsgr.application.ui.controller.fleet import BattlePreparationPage, FleetSnapshot, formation


def test_decisive_fleet_uses_formation_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    snapshot = FleetSnapshot(
        names=['A', None, None, None, None, None],
        occupied=[True, False, False, False, False, False],
    )

    def adjust(ctx: object, page: object, **kwargs: object) -> FleetSnapshot:
        captured.update(ctx=ctx, page=page, kwargs=kwargs)
        return snapshot

    monkeypatch.setattr(formation, 'adjust_fleet', adjust)
    ctx = SimpleNamespace(ctrl=MagicMock(), ocr=MagicMock())
    page = BattlePreparationPage(ctx)

    assert (
        page.adjust_fleet(
            fleet_id=None,
            fleet_rules=['A'],
            task_type='decisive',
        )
        is snapshot
    )
    assert captured['page'] is page
    assert captured['kwargs'] == {
        'fleet_id': None,
        'fleet_rules': ['A'],
        'task_type': 'decisive',
        'reset_fleet': True,
        'recognize_ship_types': True,
        'on_event': None,
    }
