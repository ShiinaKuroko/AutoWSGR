"""导出母港主页控制器及其导航目标。

上层调用：
- application.ui.navigation：执行母港页面导航。
- application.runtime：识别母港并处理主页浮层。
- business.logistics：读取母港通知状态。
- testing.ui：执行母港页面验证。

下层依赖：
- application.ui.controller.home.main_page.page：提供页面控制器和导航目标。

边界：
只导出稳定的母港页面入口，不执行页面操作或导航注册。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.home.main_page.page import HomePage, Target
from autowsgr.application.ui.controller.home.main_page.recognition import (
    check_expedition_ready,
    check_task_ready,
)


__all__ = ['HomePage', 'Target', 'check_expedition_ready', 'check_task_ready']
