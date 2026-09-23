"""验证好友页面识别和返回契约的无设备单元测试。

上层调用：
- testing：执行好友页面控制器回归测试。

下层依赖：
- application.ui.controller.sidebar.friend_page：提供好友页面稳定入口。

边界：
只验证好友页面识别委托，不连接设备或执行页面导航。
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from autowsgr.application.ui.controller.sidebar.friend_page import recognition


if TYPE_CHECKING:
    import pytest


def test_check_current_page_delegates_to_tabbed_recognition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """好友页面识别使用好友标签类型调用通用标签识别。"""
    result = MagicMock()
    checker = MagicMock(return_value=result)
    monkeypatch.setattr(recognition, 'check_tabbed_page', checker)
    screen = object()
    assert recognition.check_current_page(screen) is result

    checker.assert_called_once_with(screen, recognition.TabbedPageType.FRIEND)
