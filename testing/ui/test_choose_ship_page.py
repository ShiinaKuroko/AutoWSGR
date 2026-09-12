"""编队选船节点的规则和流程回归。"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from autowsgr.application.ui.controller.fleet.formation.ship_selection import (
    ShipSelectionPage,
    recognition,
    workflow,
)
from autowsgr.common.fleet import ShipSelector
from autowsgr.common.types import ShipType


def test_ship_name_matching_uses_normalized_pool_identity() -> None:
    assert recognition._matches_ship_name('岛风', '岛风')
    assert recognition._matches_ship_name('85工程', '85工程')
    assert not recognition._matches_ship_name('安东尼奥', '安东尼')


def test_ship_type_rule_accepts_only_expected_type() -> None:
    assert recognition._is_ship_type_in_rule(ShipType.SS, (ShipType.SS, ShipType.SSG))
    assert not recognition._is_ship_type_in_rule(ShipType.BB, (ShipType.SS, ShipType.SSG))


def test_select_ship_runs_search_and_clicks_recognized_card() -> None:
    ctx = SimpleNamespace(ctrl=MagicMock(), ocr=MagicMock())
    page = MagicMock()
    selection_page = MagicMock(spec=ShipSelectionPage)
    selector = ShipSelector(name='岛风')

    with (
        patch.object(workflow, '_open_selection_page', return_value=selection_page),
        patch.object(
            workflow.recognition,
            '_find_ship_card',
            return_value=(('岛风', 0.2, 0.3), False),
        ),
        patch.object(workflow.time, 'sleep'),
        patch.object(workflow, 'wait_leave_page'),
    ):
        result = workflow.select_ship(ctx, page, 0, (selector,))

    assert result == '岛风'
    selection_page.open_search_box.assert_called_once_with()
    selection_page.input_ship_name.assert_called_once_with('岛风')
    selection_page.dismiss_keyboard.assert_called_once_with()
    selection_page.click_ship_card.assert_called_once_with(0.2, 0.3)


def test_select_ship_rejects_empty_selector_list() -> None:
    ctx = SimpleNamespace(ctrl=MagicMock(), ocr=MagicMock())
    with pytest.raises(ValueError, match='selectors 不能为空'):
        workflow.select_ship(ctx, MagicMock(), 0, ())
