"""模块功能：导出活动地图页面控制器。

上层调用：
- application.ui.navigation：注册活动地图页面并执行页面导航。
- business.combat.bettle：进入活动地图出击流程。

下层依赖：
- application.ui.controller.home.event_page.page：提供页面控制器。

边界：
本模块只声明稳定的页面入口，不执行页面识别、设备操作或导航动作。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.home.event_page.page import BaseEventPage


__all__ = ['BaseEventPage']
