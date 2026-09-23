"""验证任务页面识别和奖励流程边界的无设备单元测试。

上层调用：
- testing：执行任务页面控制器回归测试。

下层依赖：
- application.ui.controller.operations.mission_page：提供任务页面模块入口。

边界：
只验证页面契约、任务识别去重和奖励领取分支，不连接设备或执行页面导航。
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from autowsgr.application.ui.controller.operations.mission_page import (
    MissionPage,
    MissionPanel,
    recognition,
)
from autowsgr.application.ui.controller.operations.mission_page import page as page_module


def _mission(name: str) -> recognition.MissionInfo:
    return recognition.MissionInfo(
        name=name,
        raw_text=name,
        progress=100,
        claimable=True,
        confidence=1.0,
    )


def test_check_current_page_uses_mission_tab(monkeypatch: pytest.MonkeyPatch) -> None:
    """任务页面检查使用通用标签识别的任务类型。"""
    result = MagicMock()
    checker = MagicMock(return_value=result)
    monkeypatch.setattr(page_module, 'check_tabbed_page', checker)
    screen = object()

    assert MissionPage.check_current_page(screen) is result

    checker.assert_called_once_with(screen, page_module.TabbedPageType.MISSION)


def test_page_exposes_only_complete_reward_flow() -> None:
    """页面控制器不暴露面板切换和任务读取等中间步骤。"""
    assert not hasattr(MissionPage, 'select_panel')
    assert not hasattr(MissionPage, 'read_missions')
    assert not hasattr(MissionPage, 'read_all_missions')


def test_collect_rewards_rejects_negative_scroll_limit() -> None:
    """页面入口拒绝无效的滚动次数。"""
    ctx = SimpleNamespace(ctrl=MagicMock(), ocr=MagicMock())

    with pytest.raises(ValueError, match='max_scrolls'):
        MissionPage(ctx).collect_rewards(max_scrolls=-1)


def test_collect_rewards_switches_recognizes_and_stops_without_new_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """完整奖励流程先切换面板和识别任务，再在无新任务时停止。"""
    ctrl = MagicMock()
    ctx = SimpleNamespace(ctrl=ctrl, ocr=MagicMock())
    select_panel = MagicMock()
    scroll_task_list = MagicMock()
    recognize_missions = MagicMock(
        side_effect=[[_mission('任务甲')], [_mission('任务甲')]],
    )
    monkeypatch.setattr(page_module.operations, 'select_panel', select_panel)
    monkeypatch.setattr(page_module.operations, 'scroll_task_list', scroll_task_list)
    monkeypatch.setattr(page_module.recognition, 'recognize_missions', recognize_missions)
    monkeypatch.setattr(
        page_module.recognition, 'find_reward_collect_all_button', lambda _screen: None
    )
    monkeypatch.setattr(page_module.recognition, 'find_reward_collect_button', lambda _screen: None)

    result = MissionPage(ctx).collect_rewards(MissionPanel.DAILY, max_scrolls=3)

    assert result is False
    select_panel.assert_called_once_with(ctrl, 'daily')
    scroll_task_list.assert_called_once_with(ctrl)
    assert recognize_missions.call_count == 2


def test_collect_rewards_prefers_all_rewards_and_confirms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """奖励流程优先点击一键领取，并处理随后出现的确认按钮。"""
    ctrl = MagicMock()
    reward_detail = SimpleNamespace(center=(0.2, 0.3))
    confirm_detail = SimpleNamespace(center=(0.4, 0.5))
    click_reward = MagicMock()
    click_confirm = MagicMock()
    monkeypatch.setattr(
        page_module.recognition,
        'find_reward_collect_all_button',
        lambda _screen: reward_detail,
    )
    monkeypatch.setattr(
        page_module.recognition, 'find_confirm_button', lambda _screen: confirm_detail
    )
    monkeypatch.setattr(page_module.operations, 'click_reward_button', click_reward)
    monkeypatch.setattr(page_module.operations, 'click_confirm_button', click_confirm)
    monkeypatch.setattr(page_module.time, 'sleep', lambda _seconds: None)

    ctx = SimpleNamespace(ctrl=ctrl, ocr=MagicMock())
    monkeypatch.setattr(page_module.recognition, 'recognize_missions', lambda _screen, _ocr: [])

    assert MissionPage(ctx).collect_rewards(MissionPanel.ALL, max_scrolls=0) is True

    click_reward.assert_called_once_with(ctrl, reward_detail.center)
    click_confirm.assert_called_once_with(ctrl, confirm_detail.center)


def test_collect_rewards_falls_back_to_single_reward_and_confirms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """完整奖励流程在没有一键入口时领取单个奖励并确认。"""
    ctrl = MagicMock()
    reward_detail = SimpleNamespace(center=(0.2, 0.3))
    confirm_detail = SimpleNamespace(center=(0.4, 0.5))
    click_reward = MagicMock()
    click_confirm = MagicMock()
    monkeypatch.setattr(page_module.recognition, 'recognize_missions', lambda _screen, _ocr: [])
    monkeypatch.setattr(
        page_module.recognition, 'find_reward_collect_all_button', lambda _screen: None
    )
    monkeypatch.setattr(
        page_module.recognition,
        'find_reward_collect_button',
        lambda _screen: reward_detail,
    )
    monkeypatch.setattr(
        page_module.recognition, 'find_confirm_button', lambda _screen: confirm_detail
    )
    monkeypatch.setattr(page_module.operations, 'click_reward_button', click_reward)
    monkeypatch.setattr(page_module.operations, 'click_confirm_button', click_confirm)
    monkeypatch.setattr(page_module.time, 'sleep', lambda _seconds: None)

    ctx = SimpleNamespace(ctrl=ctrl, ocr=MagicMock())

    assert MissionPage(ctx).collect_rewards(MissionPanel.DAILY, max_scrolls=0) is True

    click_reward.assert_called_once_with(ctrl, reward_detail.center)
    click_confirm.assert_called_once_with(ctrl, confirm_detail.center)
