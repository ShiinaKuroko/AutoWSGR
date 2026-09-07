"""模块功能：导出后院页面控制器及其页面导航目标。

上层调用：
- application.ui.navigation.graph.logistics：调用后院与浴室、食堂之间的页面边动作。
- application.ui.controller.home：查询后院页面识别结果。
- testing.ui：执行后院页面导航验证。

下层依赖：
- application.ui.controller.backyard.main_page.page：提供后院页面操作实现。
"""

from autowsgr.application.ui.controller.backyard.main_page.page import BackyardPage, BackyardTarget


__all__ = ['BackyardPage', 'BackyardTarget']
