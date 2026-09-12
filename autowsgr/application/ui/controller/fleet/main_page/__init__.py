"""模块功能：导出出征准备页控制器。

上层调用：
- application.ui.controller.fleet：向上层提供 Fleet 页面控制器。

下层依赖：
- main_page.page：提供准备页页面控制和主流程。
- main_page.constants：提供准备页基础页面类型。
"""

from autowsgr.application.ui.controller.fleet.main_page.constants import Panel
from autowsgr.application.ui.controller.fleet.main_page.page import BattlePreparationPage


__all__ = ['BattlePreparationPage', 'Panel']
