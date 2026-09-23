"""模块功能：导出侧边栏主页面导航控制器及其目标类型。

上层调用：
- application.ui.navigation：执行侧边栏页面导航。
- application.ui.controller.home.main_page：从母港打开侧边栏。

下层依赖：
- application.ui.controller.sidebar.main_page.page：提供侧边栏页面导航实现。

边界：
本模块只导出稳定的侧边栏导航入口，不执行页面操作或创建运行时上下文。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.sidebar.main_page.page import (
    SidebarPage,
    SidebarTarget,
)


__all__ = ['SidebarPage', 'SidebarTarget']
