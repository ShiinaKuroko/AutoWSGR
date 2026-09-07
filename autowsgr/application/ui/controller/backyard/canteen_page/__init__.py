"""模块功能：导出食堂页面控制器。

上层调用：
- business.logistics.cook：调用做菜入口。
- application.ui.navigation.graph.logistics：调用食堂返回后院的页面边动作。
- testing.ui：执行食堂页面导航和做菜验证。

下层依赖：
- application.ui.controller.backyard.canteen_page.page：提供食堂页面操作实现。
"""

from autowsgr.application.ui.controller.backyard.canteen_page.page import CanteenPage


__all__ = ['CanteenPage']
