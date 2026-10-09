"""模块功能：提供普通推图活动的坐标命名空间。

上层调用：
- application.ui.controller.home.event_page.page：读取普通推图落点。

下层依赖：
- normal.constants：保存本玩法点击坐标。

本模块只导出坐标命名空间，不放页面动作。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.home.event_page.stage_push import constants


__all__ = ['constants']
