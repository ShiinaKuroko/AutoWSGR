"""模块功能：提供出征页检查器的模块入口。

上层调用：
- application.ui.navigation：调用出征页五个标签的识别入口。

下层依赖：
- sortie.checker：提供识别入口。

本模块只导出稳定入口，不放业务实现。
"""

from __future__ import annotations

from autowsgr.application.ui.navigation.checker.sortie.checker import (
    check_campaign_page,
    check_decisive_page,
    check_exercise_page,
    check_expedition_page,
    check_sortie_page,
    read_tab_center,
)


__all__ = [
    'check_campaign_page',
    'check_decisive_page',
    'check_exercise_page',
    'check_expedition_page',
    'check_sortie_page',
    'read_tab_center',
]
