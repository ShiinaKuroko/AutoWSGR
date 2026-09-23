"""模块功能：提供 sortie_page 页面壳的稳定懒加载入口。

上层调用：
- application.ui.controller.operations.sortie_page.*_page：选择顶部业务标签。
- application.ui.navigation：进入或离开 sortie_page 页面壳。

下层依赖：
- application.ui.controller.operations.sortie_page.main_page.page：提供页面控制器和类型。

本模块只导出稳定页面入口；导入常量或原子操作时不提前加载页面识别实现。
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from autowsgr.application.ui.controller.operations.sortie_page.main_page.page import (
        SortiePage,
        SortieTab,
        TabbedPageType,
    )


__all__ = ['SortiePage', 'SortieTab', 'TabbedPageType']


def __getattr__(name: str) -> object:
    """按需加载页面入口，避免常量消费者加载识别实现。"""
    if name not in __all__:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    from autowsgr.application.ui.controller.operations.sortie_page.main_page.page import (
        SortiePage,
        SortieTab,
        TabbedPageType,
    )

    return {
        'SortiePage': SortiePage,
        'SortieTab': SortieTab,
        'TabbedPageType': TabbedPageType,
    }[name]
