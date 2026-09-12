"""模块功能：保存 sortie_page 顶部标签的业务类型和固定顺序。

上层调用：
- application.ui.controller.operations.sortie_page.main_page.page：将标签类型映射为页面坐标和索引。
- application.ui.controller.operations.sortie_page.*_page：选择对应出征模式的顶部标签。

下层依赖：
- 无。

本模块不读取截图、不操作设备，也不保存运行时状态。
"""

from __future__ import annotations

import enum


class SortieTab(enum.Enum):
    """sortie_page 顶部的五个业务标签。"""

    SORTIE = '出征'
    EXERCISE = '演习'
    EXPEDITION = '远征'
    CAMPAIGN = '战役'
    DECISIVE = '决战'


SORTIE_TAB_LIST: tuple[SortieTab, ...] = tuple(SortieTab)
"""顶部标签的显示顺序，用于把视觉索引映射为业务标签。"""

SORTIE_TAB_INDEX: dict[SortieTab, int] = {tab: index for index, tab in enumerate(SORTIE_TAB_LIST)}
"""顶部标签到视觉索引的映射，用于构造标签切换检查器。"""


__all__ = ['SORTIE_TAB_INDEX', 'SORTIE_TAB_LIST', 'SortieTab']
