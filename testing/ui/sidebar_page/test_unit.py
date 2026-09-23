"""模块功能：验证侧边栏主页面的识别和导航边界。

上层调用：
- pytest：执行侧边栏主页面的无设备单元验证。

下层依赖：
- application.ui.controller.sidebar.main_page：提供侧边栏页面控制器。
- application.ui.controller.sidebar.main_page.recognition：提供页面事实识别。
- application.ui.controller.sidebar.main_page.operations：提供二级菜单原子点击。
- common.device.interaction：提供导航配置和异常类型。

边界：
本模块只使用 mock 验证侧边栏页面契约，不连接真实设备或执行子页面业务。
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from autowsgr.application.ui.controller.sidebar.main_page import (
    SidebarPage,
    SidebarTarget,
    constants,
    page,
    recognition,
)
from autowsgr.common.types import PageName
from autowsgr.common.device.interaction import NavConfig, NavigationError


def test_check_current_page_delegates_to_recognition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """页面检查委托给侧边栏事实识别模块。"""
    screen = object()
    result = MagicMock()
    recognize = MagicMock(return_value=result)
    monkeypatch.setattr(recognition, 'recognize_sidebar_page', recognize)

    assert SidebarPage.check_current_page(screen) is result
    recognize.assert_called_once_with(screen)


def test_recognize_sidebar_page_returns_miss_without_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """未匹配模板时返回明确的侧边栏未命中事实。"""
    monkeypatch.setattr(recognition.ImageChecker, 'find_template', lambda *_args, **_kwargs: None)

    result = recognition.recognize_sidebar_page(object())

    assert result.name == PageName.SIDEBAR.value
    assert result.matched is False
    assert result.score == 0.0


def test_navigate_to_rejects_invalid_target() -> None:
    """无效目标在导入子页面和设备操作前被拒绝。"""
    ctx = MagicMock()

    with pytest.raises(TypeError, match='侧边栏目标必须为 SidebarTarget'):
        SidebarPage(ctx).navigate_to(object())

    ctx.ctrl.click.assert_not_called()


def test_navigation_uses_single_entry() -> None:
    """侧边栏目标统一由单一导航入口处理。"""
    assert hasattr(SidebarPage, 'navigate_to')
    assert not hasattr(SidebarPage, 'go_to_build')
    assert not hasattr(SidebarPage, 'go_to_intensify')
    assert not hasattr(SidebarPage, 'go_to_friend')


def test_submenu_navigation_retries_before_returning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """二级菜单导航在有限重试后返回成功。"""
    ctx = MagicMock()
    wait_for_page = MagicMock(side_effect=[NavigationError('页面未到达'), object()])
    click_sidebar_entry = MagicMock()
    click_submenu_entry = MagicMock()
    sleep = MagicMock()
    monkeypatch.setattr(page, 'wait_for_page', wait_for_page)
    monkeypatch.setattr(page, 'DEFAULT_NAV_CONFIG', NavConfig(max_retries=2, retry_delay=0.0))
    monkeypatch.setattr(page.time, 'sleep', sleep)
    monkeypatch.setattr(page.operations, 'click_sidebar_entry', click_sidebar_entry)
    monkeypatch.setattr(page.operations, 'click_submenu_entry', click_submenu_entry)

    SidebarPage(ctx)._navigate_with_submenu(SidebarTarget.BUILD, MagicMock())

    assert click_sidebar_entry.call_count == 2
    assert click_submenu_entry.call_count == 2
    assert click_sidebar_entry.call_args.args == (ctx.ctrl, constants.CLICK_BUILD)
    assert click_submenu_entry.call_args.args == (ctx.ctrl, constants.CLICK_BUILD_SUBMENU)
    assert wait_for_page.call_count == 2
    assert sleep.call_count == 3


def test_go_back_waits_for_home_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """返回母港使用返回坐标并等待母港终态。"""
    ctx = MagicMock()
    wait_for_page = MagicMock()
    monkeypatch.setattr(page, 'click_and_wait_for_page', wait_for_page)

    SidebarPage(ctx).go_back()

    wait_for_page.assert_called_once()
    assert wait_for_page.call_args.args[0] is ctx.ctrl
    assert wait_for_page.call_args.kwargs['click_coord'] == constants.CLICK_CLOSE
    assert wait_for_page.call_args.kwargs['source'] == PageName.SIDEBAR
    assert wait_for_page.call_args.kwargs['target'] == PageName.HOME
