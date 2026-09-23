"""模块功能：导出食堂页面控制器的稳定公共入口。

上层调用：
- business.logistics.cook：调用食堂做菜入口。
- application.ui.navigation.registry：注册食堂页面识别器。
- application.ui.navigation.graph.logistics：调用食堂页面回退动作。
- testing.ui：导入页面控制器执行 UI 验证。

下层依赖：
- application.ui.controller.backyard.canteen_page.page：提供页面控制器。

本模块只提供稳定公共入口，不执行页面操作或创建运行时上下文。
"""

from autowsgr.application.ui.controller.backyard.canteen_page.page import CanteenPage


__all__ = ['CanteenPage']
