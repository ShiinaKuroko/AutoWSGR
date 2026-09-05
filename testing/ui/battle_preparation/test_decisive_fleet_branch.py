"""统一编队入口的决战分支回归。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import autowsgr.application.ui.controller.battle_preparation.fleet_change.decisive as decisive_module
from autowsgr.application.ui.controller.battle_preparation import BattlePreparationPage


if TYPE_CHECKING:
    import pytest


def test_task_type_decisive_uses_decisive_fleet_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def change(page: object, names: object, *, on_event: object = None) -> bool:
        captured.update(page=page, names=names, on_event=on_event)
        return True

    monkeypatch.setattr(decisive_module, 'change_decisive_fleet', change)
    page = BattlePreparationPage(SimpleNamespace(ctrl=MagicMock(), ocr=MagicMock()))

    assert page.change_fleet(None, ['A'], task_type='decisive')
    assert captured['page'] is page
    assert captured['names'] == ['A']
