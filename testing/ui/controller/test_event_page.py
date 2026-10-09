"""模块功能：验证活动页面控制器的单击落点。

直接调用方：项目测试运行器。

直接依赖：pytest、event_page 的控制器与坐标表。

边界：用设备服务替身接管点击，不连接设备、不识别画面。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from autowsgr.application.ui.controller.home.event_page import EventPage, constants
from autowsgr.application.ui.controller.home.event_page.stage_push import constants as stage_push_constants


class _Ctrl:
    """设备服务替身，记录点击落点。"""

    def __init__(self) -> None:
        self.clicks: list[tuple[float, float]] = []

    def click(self, x: float, y: float, *, delay: bool = False) -> None:
        self.clicks.append((x, y))


def _build(event_type: str = 'stage_push') -> tuple[EventPage, _Ctrl]:
    """构造控制器与记录点击的替身。"""
    ctrl = _Ctrl()
    ctx: Any = SimpleNamespace(runtime=SimpleNamespace(ctrl=ctrl))
    return EventPage(ctx, event_type=event_type), ctrl


@pytest.mark.parametrize('node', [1, 3, 6])
def test_go_to_overlay_clicks_stage_position(node: int) -> None:
    """按落点序号点击对应坐标。"""
    page, ctrl = _build()

    page.go_to_overlay(node)

    assert ctrl.clicks == [stage_push_constants.STAGE_POSITIONS[node]]


@pytest.mark.parametrize('node', [0, 7, -1])
def test_go_to_overlay_rejects_invalid_node(node: int) -> None:
    """非法落点序号被拒绝。"""
    page, _ = _build()

    with pytest.raises(ValueError):
        page.go_to_overlay(node)


def test_switch_difficulty_uses_recognized_center() -> None:
    """难度按钮使用识别产出的中心。"""
    page, ctrl = _build()

    page.switch_difficulty((0.5, 0.25))

    assert ctrl.clicks == [(0.5, 0.25)]


def test_go_to_prepare_prefers_recognized_center() -> None:
    """确认出征优先使用识别产出的中心。"""
    page, ctrl = _build()

    page.go_to_prepare((0.4, 0.8))

    assert ctrl.clicks == [(0.4, 0.8)]


def test_go_to_prepare_falls_back_without_center() -> None:
    """没有识别结果时使用兜底落点。"""
    page, ctrl = _build()

    page.go_to_prepare()

    assert ctrl.clicks == [stage_push_constants.CLICK_SORTIE_PREPARE_FALLBACK]


def test_back_actions_use_fixed_positions() -> None:
    """关浮窗与回首页使用固定落点。"""
    page, ctrl = _build()

    page.click_overlay_close()
    page.go_back()

    assert ctrl.clicks == [constants.CLICK_OVERLAY_CLOSE, constants.CLICK_HOME_BACK]


def test_unknown_event_type_is_rejected() -> None:
    """未支持的玩法被拒绝。"""
    page, _ = _build(event_type='assault')

    with pytest.raises(ValueError):
        page.go_to_overlay(1)
