"""模块功能：验证主页控制器的单击落点。

直接调用方：项目测试运行器。

直接依赖：pytest、main_page 的控制器与坐标表。

边界：用设备服务替身接管点击，不连接设备、不识别画面。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from autowsgr.application.ui.controller.home.main_page import HomePage, Target, constants


class _Ctrl:
    """设备服务替身，记录点击落点。"""

    def __init__(self) -> None:
        self.clicks: list[tuple[float, float]] = []

    def click(self, x: float, y: float, *, delay: bool = False) -> None:
        self.clicks.append((x, y))


def _build() -> tuple[HomePage, _Ctrl]:
    """构造控制器与记录点击的替身。"""
    ctrl = _Ctrl()
    ctx: Any = SimpleNamespace(runtime=SimpleNamespace(ctrl=ctrl))
    return HomePage(ctx), ctrl


@pytest.mark.parametrize('target', list(Target))
def test_go_to_clicks_nav_position(target: Target) -> None:
    """每个导航目标点击对应落点。"""
    page, ctrl = _build()

    page.go_to(target)

    assert ctrl.clicks == [constants.NAV_POSITIONS[target.name.lower()]]


def test_go_to_rejects_missing_position(monkeypatch: pytest.MonkeyPatch) -> None:
    """目标没有配置落点时被拒绝。"""
    page, _ = _build()
    monkeypatch.delitem(constants.NAV_POSITIONS, 'event')

    with pytest.raises(ValueError):
        page.go_to(Target.EVENT)


def test_news_checkbox_uses_recognized_center() -> None:
    """公告勾选框使用识别产出的中心。"""
    page, ctrl = _build()

    page.click_news_checkbox((0.05, 0.9))

    assert ctrl.clicks == [(0.05, 0.9)]


def test_news_close_uses_fixed_position() -> None:
    """关闭公告使用固定落点。"""
    page, ctrl = _build()

    page.click_news_close()

    assert ctrl.clicks == [constants.DISMISS_POSITIONS['news_close']]


def test_reward_claim_uses_recognized_center() -> None:
    """领取奖励使用识别产出的中心。"""
    page, ctrl = _build()

    page.click_reward_claim((0.5, 0.66))

    assert ctrl.clicks == [(0.5, 0.66)]


def test_reward_confirm_uses_recognized_center() -> None:
    """确认奖励使用识别产出的中心。"""
    page, ctrl = _build()

    page.click_reward_confirm((0.5, 0.57))

    assert ctrl.clicks == [(0.5, 0.57)]
