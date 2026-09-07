"""模块功能：导出好友页面控制器。

上层调用：
- application.ui.navigation：从侧边栏进入好友页面并返回。
- testing.ui：执行好友页面导航验证。

下层依赖：
- application.ui.controller.sidebar.friend_page.page：提供好友页面操作实现。
"""

from autowsgr.application.ui.controller.sidebar.friend_page.page import FriendPage


__all__ = ['FriendPage']
