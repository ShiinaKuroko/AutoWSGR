"""模块功能：提供餐厅二级页控制器的模块入口。

上层调用：
- application.ui.navigation：调用该页控制器执行回首页与退回。

下层依赖：
- canteen_page.page：提供页面控制器。

本模块只导出稳定入口，不放业务实现。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.backyard.canteen_page.page import CanteenPage


__all__ = ['CanteenPage']
