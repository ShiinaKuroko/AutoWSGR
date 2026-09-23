"""Homepage overlay state transition tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from autowsgr.application.ui.controller.home.main_page import operations
from autowsgr.application.ui.controller.home.main_page import page as page_module
from autowsgr.application.ui.controller.home.main_page.recognition import OverlayKind


if TYPE_CHECKING:
    import pytest


def test_home_page_checks_checkbox_before_closing_news(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Announcement flow checks both checkbox states before one close click."""
    ctrl = SimpleNamespace(screenshot=MagicMock())
    page = page_module.HomePage(SimpleNamespace(ctrl=ctrl, record_screenshot=MagicMock()))
    overlays = MagicMock(
        side_effect=[
            SimpleNamespace(kind=OverlayKind.NEWS),
            SimpleNamespace(kind=OverlayKind.NEWS),
            None,
            None,
            None,
            None,
        ],
    )
    checkbox = MagicMock(
        side_effect=[
            SimpleNamespace(checked=False),
            SimpleNamespace(checked=True),
        ],
    )
    click_checkbox = MagicMock()
    click_close = MagicMock()

    monkeypatch.setattr(page_module.recognition, 'read_overlay_match', overlays)
    monkeypatch.setattr(page_module.recognition, 'read_news_checkbox_match', checkbox)
    monkeypatch.setattr(page_module.recognition, 'match_center', MagicMock(return_value=(0.5, 0.5)))
    monkeypatch.setattr(operations, 'click_news_checkbox', click_checkbox)
    monkeypatch.setattr(operations, 'click_news_close', click_close)

    assert page.dismiss_current_overlay() is True
    assert overlays.call_count == 6
    assert checkbox.call_count == 2
    click_checkbox.assert_called_once()
    click_close.assert_called_once_with(ctrl)


def test_home_page_claims_reward_and_verifies_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reward flow clicks recognized targets and verifies confirmation removal."""
    ctrl = SimpleNamespace(screenshot=MagicMock())
    page = page_module.HomePage(SimpleNamespace(ctrl=ctrl, record_screenshot=MagicMock()))
    reward = SimpleNamespace(kind=OverlayKind.REWARD)
    confirmation = SimpleNamespace(kind=OverlayKind.REWARD_CONFIRM)
    overlays = MagicMock(side_effect=[reward, None, None, None])
    claim = MagicMock(return_value=SimpleNamespace(kind=OverlayKind.REWARD))
    confirmations = MagicMock(side_effect=[confirmation, None])
    click_claim = MagicMock()
    click_confirmation = MagicMock()

    monkeypatch.setattr(page_module.recognition, 'read_overlay_match', overlays)
    monkeypatch.setattr(page_module.recognition, 'read_reward_claim_match', claim)
    monkeypatch.setattr(page_module.recognition, 'read_reward_confirmation_match', confirmations)
    monkeypatch.setattr(page_module.recognition, 'match_center', MagicMock(return_value=(0.5, 0.5)))
    monkeypatch.setattr(operations, 'click_reward_claim', click_claim)
    monkeypatch.setattr(operations, 'click_reward_confirmation', click_confirmation)

    assert page.dismiss_current_overlay() is True
    assert overlays.call_count == 4
    assert claim.call_count == 1
    assert confirmations.call_count == 2
    click_claim.assert_called_once()
    click_confirmation.assert_called_once()
