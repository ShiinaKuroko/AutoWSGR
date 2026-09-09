"""模块功能：导出游戏登录前启动画面的页面控制器。

上层调用：
- application.runtime.startup：等待启动画面并点击进入游戏。
- application.runtime.initialize.initialize：冷启动时完成启动画面识别和进入操作。

下层依赖：
- application.ui.controller.login.page：提供启动画面检查和点击进入行为。
"""

from autowsgr.application.ui.controller.login.page import LoginPage


__all__ = ['LoginPage']
