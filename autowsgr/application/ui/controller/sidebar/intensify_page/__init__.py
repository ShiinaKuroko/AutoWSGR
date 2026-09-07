"""模块功能：导出强化页面控制器及其标签类型。

上层调用：
- application.ui.navigation：从侧边栏进入强化页面并返回。
- testing.ui：执行强化页面导航和标签验证。

下层依赖：
- application.ui.controller.sidebar.intensify_page.page：提供强化页面操作实现。
"""

from autowsgr.application.ui.controller.sidebar.intensify_page.page import (
    IntensifyPage,
    IntensifyTab,
)


__all__ = ['IntensifyPage', 'IntensifyTab']
