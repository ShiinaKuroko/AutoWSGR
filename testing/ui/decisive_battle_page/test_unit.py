from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, call

import numpy as np
import pytest

from autowsgr.application.ui.controller.operations.sortie_page.decisive_page import (
    DecisiveBattlePage,
    DecisiveMapController,
)
from autowsgr.application.ui.controller.operations.sortie_page.decisive_page import (
    map_page as map_page_module,
)
from autowsgr.application.ui.controller.operations.sortie_page.decisive_page import (
    page as page_module,
)
from autowsgr.application.ui.controller.operations.sortie_page.decisive_page.constants import (
    ADVANCE_CARD_POSITIONS,
    CLICK_ADVANCE_CONFIRM,
)


def test_recognize_stage_returns_first_incomplete_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = iter([True, False, True])
    monkeypatch.setattr(
        page_module.PixelChecker,
        'check_pixel',
        lambda *_args, **_kwargs: next(values),
    )

    assert DecisiveBattlePage.recognize_stage(np.zeros((720, 1280, 3), dtype=np.uint8), 6) == 1


def test_recognize_stage_returns_none_after_refresh_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(page_module.PixelChecker, 'check_pixel', lambda *_args, **_kwargs: True)
    monkeypatch.setattr(page_module.ImageChecker, 'template_exists', lambda *_args, **_kwargs: True)

    assert DecisiveBattlePage.recognize_stage(np.zeros((720, 1280, 3), dtype=np.uint8), 6) is None


def test_reset_chapter_refuses_unrecognized_button(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = object.__new__(DecisiveBattlePage)
    page._ctrl = MagicMock()
    clock = iter([0.0, 6.0])
    monkeypatch.setattr(page_module.time, 'monotonic', lambda: next(clock))
    monkeypatch.setattr(page_module.time, 'sleep', lambda _delay: None)
    monkeypatch.setattr(page_module.ImageChecker, 'find_template', lambda *_args, **_kwargs: None)

    with pytest.raises(TimeoutError, match='拒绝点击'):
        page.reset_chapter()

    page._ctrl.click.assert_not_called()


def test_reset_chapter_clicks_only_a_recognized_button(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = object.__new__(DecisiveBattlePage)
    page._ctrl = MagicMock()
    match = SimpleNamespace(center=(0.5, 0.5))
    monkeypatch.setattr(page_module.time, 'monotonic', lambda: 0.0)
    monkeypatch.setattr(page_module.time, 'sleep', lambda _delay: None)
    monkeypatch.setattr(page_module.ImageChecker, 'find_template', lambda *_args, **_kwargs: match)
    monkeypatch.setattr(
        page_module.ImageChecker, 'template_exists', lambda *_args, **_kwargs: False
    )
    monkeypatch.setattr(page_module, 'confirm_operation', MagicMock())

    assert page.reset_chapter() is True
    page._ctrl.click.assert_called_once_with(0.5, 0.5)
    page_module.confirm_operation.assert_called_once_with(
        page._ctrl,
        must_confirm=True,
        timeout=5.0,
    )


def test_enter_formation_refuses_unrecognized_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = object.__new__(DecisiveMapController)
    controller._ctrl = MagicMock()
    monkeypatch.setattr(map_page_module.time, 'sleep', lambda _delay: None)
    monkeypatch.setattr(map_page_module, 'check_decisive_map_page', lambda _screen: False)

    with pytest.raises(TimeoutError, match='未识别到决战地图页'):
        controller.enter_formation()

    controller._ctrl.click.assert_not_called()


def test_select_advance_card_waits_for_recognized_overlay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = object.__new__(DecisiveMapController)
    controller._ctrl = MagicMock()
    controller.wait_for_overlay = MagicMock()
    monkeypatch.setattr(map_page_module.time, 'sleep', lambda _delay: None)

    controller.select_advance_card(0)

    controller.wait_for_overlay.assert_called_once()
    assert controller._ctrl.click.call_args_list == [
        call(*ADVANCE_CARD_POSITIONS[0]),
        call(*CLICK_ADVANCE_CONFIRM),
    ]


def test_select_advance_card_rejects_invalid_index() -> None:
    controller = object.__new__(DecisiveMapController)
    controller._ctrl = MagicMock()

    with pytest.raises(ValueError, match='索引无效'):
        controller.select_advance_card(-1)

    controller._ctrl.click.assert_not_called()


def test_use_last_fleet_refuses_unrecognized_button(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = object.__new__(DecisiveMapController)
    controller._ctrl = MagicMock()
    clock = iter([0.0, 6.0])
    monkeypatch.setattr(map_page_module.time, 'monotonic', lambda: next(clock))
    monkeypatch.setattr(map_page_module.time, 'sleep', lambda _delay: None)
    monkeypatch.setattr(
        map_page_module.ImageChecker, 'find_template', lambda *_args, **_kwargs: None
    )

    with pytest.raises(TimeoutError, match='拒绝点击'):
        controller.click_use_last_fleet()

    controller._ctrl.click.assert_not_called()


def test_wait_for_entry_phase_returns_freshly_recognized_phase() -> None:
    controller = object.__new__(DecisiveMapController)
    controller._wait_for_use_last_fleet = MagicMock(return_value=False)
    controller._wait_for_advance_choice = MagicMock(return_value=False)
    controller.read_decisive_phase = MagicMock(
        return_value=map_page_module.DecisivePhase.PREPARE_COMBAT,
    )

    result = controller.wait_for_entry_phase(
        wait_for_use_last=True,
        wait_for_advance=True,
        wait_for_fleet=False,
        timeout=0.1,
        interval=0.01,
    )

    assert result is map_page_module.DecisivePhase.PREPARE_COMBAT
    controller._wait_for_use_last_fleet.assert_called_once()
    controller._wait_for_advance_choice.assert_called_once()
    controller.read_decisive_phase.assert_called_once_with(
        advance_choice_roi=None,
        allow_fleet_overlay=False,
    )


def test_read_decisive_phase_can_disable_fleet_overlay_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = object.__new__(DecisiveMapController)
    controller._ctrl = MagicMock()
    detected: list[dict[str, object]] = []
    controller._ctrl.screenshot.return_value = np.zeros((720, 1280, 3), dtype=np.uint8)
    monkeypatch.setattr(
        map_page_module.ImageChecker,
        'template_exists',
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        map_page_module,
        'detect_decisive_overlay',
        lambda _screen, **kwargs: detected.append(kwargs) or None,
    )
    monkeypatch.setattr(map_page_module, 'check_decisive_map_page', lambda _screen: False)

    assert controller.read_decisive_phase(allow_fleet_overlay=False) is None

    assert detected == [{'advance_choice_roi': None, 'include_fleet_acquisition': False}]


def test_read_decisive_phase_blocks_confirm_exit_overlay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = object.__new__(DecisiveMapController)
    controller._ctrl = MagicMock()
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    controller._ctrl.screenshot.return_value = screen
    monkeypatch.setattr(
        map_page_module.ImageChecker,
        'template_exists',
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        map_page_module,
        'detect_decisive_overlay',
        lambda *_args, **_kwargs: map_page_module.DecisiveOverlay.CONFIRM_EXIT,
    )
    map_check = MagicMock(return_value=True)
    monkeypatch.setattr(map_page_module, 'check_decisive_map_page', map_check)

    assert controller.read_decisive_phase() is None
    map_check.assert_not_called()


def test_read_decisive_phase_rejects_stale_fleet_overlay_on_map_recheck(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = object.__new__(DecisiveMapController)
    controller._ctrl = MagicMock()
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    controller._ctrl.screenshot.side_effect = [screen, screen]
    monkeypatch.setattr(
        map_page_module.ImageChecker,
        'template_exists',
        lambda *_args, **_kwargs: False,
    )
    detected = iter([None, map_page_module.DecisiveOverlay.FLEET_ACQUISITION])
    monkeypatch.setattr(
        map_page_module,
        'detect_decisive_overlay',
        lambda *_args, **_kwargs: next(detected),
    )
    monkeypatch.setattr(map_page_module, 'check_fleet_acquisition', lambda _screen: False)
    map_check = MagicMock(return_value=True)
    monkeypatch.setattr(map_page_module, 'check_decisive_map_page', map_check)
    monkeypatch.setattr(map_page_module.time, 'sleep', lambda _delay: None)

    assert controller.read_decisive_phase() is None
    map_check.assert_called_once_with(screen)


def test_close_fleet_overlay_refuses_when_overlay_is_gone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = object.__new__(DecisiveMapController)
    controller._ctrl = MagicMock()
    monkeypatch.setattr(map_page_module, 'check_fleet_acquisition', lambda _screen: False)

    assert controller.close_fleet_overlay() is False
    controller._ctrl.click.assert_not_called()


def test_read_node_keeps_none_icon_retry_as_a_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = object.__new__(DecisiveMapController)
    monkeypatch.setattr(map_page_module, 'get_api_dll', MagicMock(return_value=object()))
    monkeypatch.setattr(map_page_module.time, 'sleep', lambda _delay: None)
    controller.read_ship_icon_position_with_retry = MagicMock(side_effect=[0.5, None, None])

    with pytest.raises(RuntimeError, match='舰船指示器'):
        controller.read_node()


def test_read_fleet_skips_ship_pool_for_non_empty_formation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = object.__new__(DecisiveMapController)
    controller._ctx = object()
    controller._ctrl = MagicMock()
    controller._ocr = object()
    controller.enter_formation = MagicMock()
    page = MagicMock()
    page.read_fleet_snapshot.return_value = SimpleNamespace(
        names=['U-47', None, None, None, None, None]
    )
    page.read_ship_damage.return_value = {}

    monkeypatch.setattr(map_page_module, 'BattlePreparationPage', lambda _ctx: page)
    result = controller.read_fleet()

    assert result == (['U-47', None, None, None, None, None], {}, {'U-47'})
    page.click_ship_slot.assert_not_called()


def test_read_fleet_refuses_to_scan_when_ship_list_did_not_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = object.__new__(DecisiveMapController)
    controller._ctx = object()
    controller._ctrl = MagicMock()
    controller._ocr = object()
    controller.enter_formation = MagicMock()
    controller._ctrl.screenshot.return_value = np.zeros((720, 1280, 3), dtype=np.uint8)
    page = MagicMock()
    page.read_fleet_snapshot.return_value = SimpleNamespace(
        names=[None, None, None, None, None, None]
    )
    page.read_ship_damage.return_value = {}
    monkeypatch.setattr(map_page_module, 'BattlePreparationPage', lambda _ctx: page)
    clock = iter([0.0, 6.0])
    monkeypatch.setattr(map_page_module.time, 'monotonic', lambda: next(clock))
    monkeypatch.setattr(map_page_module.time, 'sleep', lambda _delay: None)

    with pytest.raises(TimeoutError, match='拒绝继续扫描'):
        controller.read_fleet()

    page.click_ship_slot.assert_called_once_with(0)
