"""模块功能：提供侧边栏主页面的模块入口。

上层调用：
- application.ui.navigation：调用侧边栏页面控制器执行导航。

下层依赖：
- sidebar.main_page.page：提供侧边栏页面控制器与目标类型。

本模块只导出稳定入口，不放业务实现。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.sidebar.main_page.page import (
    SidebarPage,
    SidebarTarget,
)


__all__ = ['SidebarPage', 'SidebarTarget']
