"""兼容 shim — 实现已迁移至 :mod:`autowsgr.infra.base.ui.pages.tabbed_page`。"""

from autowsgr.infra.base.ui.pages.tabbed_page import (
    TabbedPageType,
    check_tabbed_page,
    get_active_tab_index,
    make_tab_checker,
)

__all__ = [
    'TabbedPageType',
    'check_tabbed_page',
    'get_active_tab_index',
    'make_tab_checker',
]
