"""模块功能：导出建造页面控制器及其标签类型。

上层调用：
- business.logistics.build：调用建造收取和新建造入口。
- business.logistics.destroy：调用解体标签和解装流程入口。
- application.ui.navigation.registry：注册建造页面检查器。

下层依赖：
- application.ui.controller.build_page.page：提供页面操作实现。
"""

from autowsgr.application.ui.controller.build_page.page import BuildPage, BuildTab


__all__ = ['BuildPage', 'BuildTab']
