"""验证后院页面识别的无设备单元测试。

上层调用：
- testing：执行后院页面识别回归测试。

下层依赖：
- application.ui.controller.backyard.main_page.recognition：提供后院页面识别入口。

边界：
只验证模板命中和未命中结果，不连接设备或执行页面导航。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from autowsgr.application.ui.controller.backyard.main_page import recognition
from autowsgr.common.types import PageName


if TYPE_CHECKING:
    import pytest


def test_check_current_page_returns_template_match(monkeypatch: pytest.MonkeyPatch) -> None:
    """模板命中时返回带页面名称和置信度的匹配结果。"""
    monkeypatch.setattr(
        recognition.vision.ImageChecker,
        'find_template',
        lambda *_args, **_kwargs: SimpleNamespace(confidence=0.91),
    )

    result = recognition.check_current_page(MagicMock())

    assert result.name == PageName.BACKYARD.value
    assert result.matched is True
    assert result.score == 0.91


def test_check_current_page_returns_miss_without_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """模板未命中时返回未匹配结果。"""
    monkeypatch.setattr(
        recognition.vision.ImageChecker,
        'find_template',
        lambda *_args, **_kwargs: None,
    )

    result = recognition.check_current_page(MagicMock())

    assert result == recognition.vision.PageMatch(
        name=PageName.BACKYARD.value,
        matched=False,
        score=0.0,
    )
