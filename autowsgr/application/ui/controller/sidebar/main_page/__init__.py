"""模块功能：导出侧边栏主页面控制器及其导航目标。

上层调用：
- application.ui.navigation：执行侧边栏页面导航。
- application.ui.controller.home.main_page：从母港打开侧边栏。

下层依赖：
- application.ui.controller.sidebar.main_page.page：提供侧边栏页面操作实现。
"""

from autowsgr.application.ui.controller.sidebar.main_page.page import SidebarPage, SidebarTarget


__all__ = ['SidebarPage', 'SidebarTarget']
