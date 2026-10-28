"""模块功能：提供侧边栏检查器的模块入口。

上层调用：
- application.ui.navigation：调用侧边栏、建造、强化的页面确认入口。

下层依赖：
- sidebar.checker：提供识别入口。

本模块只导出稳定入口，不放业务实现。
"""

from autowsgr.application.ui.navigation.checker.sidebar.checker import (
    check_build_submenu,
    check_intensify_submenu,
    check_sidebar_page,
)


__all__ = [
    'check_build_submenu',
    'check_intensify_submenu',
    'check_sidebar_page',
]
