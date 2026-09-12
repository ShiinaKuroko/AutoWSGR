"""sortie_page 页面壳和顶部标签的稳定入口。"""

from autowsgr.application.ui.controller.operations.sortie_page.main_page.data import SortieTab
from autowsgr.application.ui.controller.operations.sortie_page.main_page.page import (
    SortiePage,
    TabbedPageType,
    check_tab_bar,
    check_tabbed_page,
    create_page_checker,
    create_tab_checker,
    read_active_tab_index,
    read_page_type,
)


__all__ = [
    'SortiePage',
    'SortieTab',
    'TabbedPageType',
    'check_tab_bar',
    'check_tabbed_page',
    'create_page_checker',
    'create_tab_checker',
    'read_active_tab_index',
    'read_page_type',
]
