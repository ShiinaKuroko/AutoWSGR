"""食堂页面控制器的单元测试。"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from autowsgr.application.ui.controller.backyard.canteen_page import constants, operations
from autowsgr.application.ui.controller.backyard.canteen_page import page as page_module
from autowsgr.common.types import PageName


def _page() -> tuple[page_module.CanteenPage, MagicMock]:
    ctrl = MagicMock()
    return page_module.CanteenPage(SimpleNamespace(ctrl=ctrl)), ctrl


def test_select_recipe_uses_calibrated_position() -> None:
    _, ctrl = _page()

    operations.click_recipe(ctrl, constants.RECIPE_POSITIONS[2])

    ctrl.click.assert_called_once_with(*constants.RECIPE_POSITIONS[2])


def test_select_recipe_rejects_unknown_position() -> None:
    page, ctrl = _page()

    with pytest.raises(ValueError, match='菜谱编号必须为 1-3'):
        page.cook(4)

    ctrl.click.assert_not_called()


def test_cook_keeps_successful_page_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page, ctrl = _page()
    cook_button = SimpleNamespace(center=(0.2, 0.3))
    monkeypatch.setattr(
        page_module.ImageChecker, 'find_template', lambda *_args, **_kwargs: cook_button
    )
    monkeypatch.setattr(
        page_module.ImageChecker, 'template_exists', lambda *_args, **_kwargs: False
    )
    monkeypatch.setattr(page_module.time, 'sleep', lambda _seconds: None)

    assert page.cook(1) is True
    assert ctrl.click.call_args_list == [
        call(*constants.RECIPE_POSITIONS[1]),
        call(*cook_button.center),
        call(*constants.CLICK_SKIP_ANIMATION),
    ]


def test_cook_cancels_when_existing_effect_is_kept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page, ctrl = _page()
    cook_button = SimpleNamespace(center=(0.2, 0.3))
    monkeypatch.setattr(
        page_module.ImageChecker, 'find_template', lambda *_args, **_kwargs: cook_button
    )
    monkeypatch.setattr(page_module.ImageChecker, 'template_exists', lambda *_args, **_kwargs: True)
    monkeypatch.setattr(page_module.time, 'sleep', lambda _seconds: None)

    assert page.cook(1) is False
    assert ctrl.click.call_args_list == [
        call(*constants.RECIPE_POSITIONS[1]),
        call(*cook_button.center),
        call(*constants.CLICK_CANCEL_COOK),
        call(*constants.CLICK_DISMISS_POPUP),
    ]


def test_cook_force_override_closes_when_no_times_remain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page, ctrl = _page()
    cook_button = SimpleNamespace(center=(0.2, 0.3))
    monkeypatch.setattr(
        page_module.ImageChecker, 'find_template', lambda *_args, **_kwargs: cook_button
    )
    monkeypatch.setattr(page_module.ImageChecker, 'template_exists', lambda *_args, **_kwargs: True)
    monkeypatch.setattr(page_module.time, 'sleep', lambda _seconds: None)

    assert page.cook(1, force_cook=True) is False
    assert ctrl.click.call_args_list == [
        call(*constants.RECIPE_POSITIONS[1]),
        call(*cook_button.center),
        call(*constants.CLICK_FORCE_COOK),
        call(*constants.CLICK_DISMISS_POPUP),
    ]


def test_go_back_stays_page_owned_and_targets_backyard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page, ctrl = _page()
    calls: list[tuple[object, dict[str, object]]] = []
    backyard_module = SimpleNamespace(
        BackyardPage=SimpleNamespace(check_current_page=MagicMock()),
    )

    def capture_navigation(device: object, **kwargs: object) -> None:
        calls.append((device, kwargs))

    monkeypatch.setitem(
        sys.modules,
        'autowsgr.application.ui.controller.backyard.main_page',
        backyard_module,
    )
    monkeypatch.setattr(page_module, 'click_and_wait_for_page', capture_navigation)

    page.go_back()

    assert len(calls) == 1
    device, kwargs = calls[0]
    assert device is ctrl
    assert kwargs['click_coord'] == constants.CLICK_BACK
    assert kwargs['target'] is PageName.BACKYARD
    assert callable(kwargs['checker'])
