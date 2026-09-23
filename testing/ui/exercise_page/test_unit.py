"""模块功能：验证演习页面的状态读取和挑战边界。

上层调用：
- pytest：执行演习页面模块的无设备单元检查。

下层依赖：
- application.ui.controller.operations.sortie_page.exercise_page：提供页面门面和下层能力。

边界：
本模块只使用 mock 控制器验证页面编排，不连接真实设备或修改业务层调用方。
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from autowsgr.application.ui.controller.operations.sortie_page.exercise_page import (
    ExercisePage,
)
from autowsgr.application.ui.controller.operations.sortie_page.exercise_page import (
    page as page_module,
)


def _make_page() -> tuple[ExercisePage, MagicMock]:
    """创建绑定 mock 控制器的演习页面。"""
    ctrl = MagicMock()
    ctx = SimpleNamespace(ctrl=ctrl, ocr=MagicMock(), ui_stack=MagicMock())
    return ExercisePage(ctx), ctrl


def test_read_status_reads_first_four_then_fifth_rival(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """状态读取先读顶部四个对手，再滑到底部读取第五个对手。"""
    page, ctrl = _make_page()
    first_screen = object()
    second_screen = object()
    ctrl.screenshot.side_effect = [first_screen, second_screen]
    check_available = MagicMock(side_effect=[True, False, True, False, True])
    swipe_top = MagicMock()
    swipe_bottom = MagicMock()
    monkeypatch.setattr(page_module.recognition, 'check_rival_list_at_top', lambda _: True)
    monkeypatch.setattr(
        page_module.recognition,
        'check_rival_challenge_available',
        check_available,
    )
    monkeypatch.setattr(page_module.operations, 'swipe_rival_list_to_top', swipe_top)
    monkeypatch.setattr(page_module.operations, 'swipe_rival_list_to_bottom', swipe_bottom)

    status = page.read_exercise_rival_status()

    assert status.rivals == [True, False, True, False, True]
    assert status.challengeable_count == 3
    assert status.first_challengeable() == 1
    swipe_top.assert_not_called()
    swipe_bottom.assert_called_once_with(ctrl)
    assert check_available.call_args_list[-1].args == (second_screen, 3)


def test_challenge_rival_fifth_slot_moves_to_bottom(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """挑战第五个对手时定位到底部第四个可见槽位。"""
    page, ctrl = _make_page()
    ctrl.screenshot.return_value = object()
    swipe_bottom = MagicMock()
    click_rival = MagicMock()
    click_rival_refresh = MagicMock()
    click_start_battle = MagicMock()
    wait_for_page = MagicMock()
    monkeypatch.setattr(
        page_module.recognition,
        'check_rival_list_at_bottom',
        MagicMock(return_value=False),
    )
    monkeypatch.setattr(page_module.operations, 'swipe_rival_list_to_bottom', swipe_bottom)
    monkeypatch.setattr(page_module.operations, 'click_rival', click_rival)
    monkeypatch.setattr(page_module.operations, 'click_rival_refresh', click_rival_refresh)
    monkeypatch.setattr(page_module.operations, 'click_start_battle', click_start_battle)
    monkeypatch.setattr(page_module, 'wait_for_page', wait_for_page)
    monkeypatch.setattr(page_module.time, 'sleep', lambda _seconds: None)

    page.challenge_rival(5, refresh_rival=True)

    click_rival_refresh.assert_called_once_with(ctrl)
    swipe_bottom.assert_called_once_with(ctrl)
    click_rival.assert_called_once_with(ctrl, 3)
    click_start_battle.assert_called_once_with(ctrl)
    wait_for_page.assert_called_once()


def test_challenge_rival_rejects_invalid_index_before_device_access() -> None:
    """无效对手序号在任何截图和设备操作前被拒绝。"""
    page, ctrl = _make_page()

    with pytest.raises(ValueError, match='1-5'):
        page.challenge_rival(6)

    ctrl.screenshot.assert_not_called()
    ctrl.click.assert_not_called()


def test_page_does_not_expose_intermediate_rival_steps() -> None:
    """页面门面不暴露中间拼装入口，挑战流程集中在一个页面方法内。"""
    assert not hasattr(ExercisePage, 'select_exercise_rival')
    assert not hasattr(ExercisePage, 'enter_exercise_battle')
    assert not hasattr(ExercisePage, 'read_rival_formation')
    assert not hasattr(ExercisePage, 'refresh_rival')
