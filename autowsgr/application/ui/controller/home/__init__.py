"""模块功能：导出母港主页控制器及其页面导航目标。

上层调用：
- application.ui.navigation：执行母港到地图、任务、后院、侧边栏和活动页面的导航。
- application.runtime：识别母港并处理每日浮层。
- business.logistics：读取任务和远征通知状态。
- testing.ui：执行母港页面的导航验证。

下层依赖：
- application.ui.controller.home.page：提供母港页面操作实现。
"""

from autowsgr.application.ui.controller.home.page import HomePage, Target


__all__ = ['HomePage', 'Target']
