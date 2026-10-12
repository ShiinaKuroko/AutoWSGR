"""模块功能：提供改造页检查器的模块入口。

上层调用：
- application.ui.navigation：调用改造页与标签的确认入口。

下层依赖：
- intensify.checker：提供识别入口。

本模块只导出稳定入口，不放业务实现。
"""

from __future__ import annotations

from autowsgr.application.ui.navigation.checker.sidebar.intensify.checker import (
    check_intensify_page,
    check_remold_tab,
    check_skill_tab,
)


__all__ = ['check_intensify_page', 'check_remold_tab', 'check_skill_tab']
