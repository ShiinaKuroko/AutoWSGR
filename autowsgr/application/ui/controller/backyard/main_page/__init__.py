"""导出后院主页面控制器和导航目标。

上层调用：
- application.ui.navigation.graph.logistics：执行后院页面边动作。
- application.ui.controller.home.main_page：取得后院页面检查器。
- testing.ui：执行后院页面导航验证。

下层依赖：
- application.ui.controller.backyard.main_page.page：提供页面控制器和导航目标。

边界：
只导出稳定页面入口，不执行页面操作、导航注册或运行时逻辑。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.backyard.main_page.page import BackyardPage, BackyardTarget


__all__ = ['BackyardPage', 'BackyardTarget']
