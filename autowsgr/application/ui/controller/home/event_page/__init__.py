"""模块功能：导出活动地图页面控制器。

上层调用：
- application.ui.controller.home.main_page.page：取得活动页面检查器。
- business.combat：执行活动节点选择和出击准备。

下层依赖：
- application.ui.controller.home.event_page.page：提供活动地图页面操作。
"""

from autowsgr.application.ui.controller.home.event_page.page import BaseEventPage


__all__ = ['BaseEventPage']
