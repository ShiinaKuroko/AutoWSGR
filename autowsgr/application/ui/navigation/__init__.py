"""UI 语义导航公开入口。

页面控制器和视觉识别器属于下层实现；业务只请求目标页面或安全锚点，
由这里的导航服务负责识别、寻路和交接。
"""

from autowsgr.application.ui.navigation.graph import NAV_GRAPH, NavEdge, find_path, neighbors
from autowsgr.application.ui.navigation.registry import (
    get_current_page,
    get_registered_pages,
    register_default_pages,
    register_page,
)
from autowsgr.application.ui.navigation.service import goto_page, identify_current_page
from autowsgr.application.ui.navigation.stack import UIStack


__all__ = [
    'NAV_GRAPH',
    'NavEdge',
    'UIStack',
    'find_path',
    'get_current_page',
    'get_registered_pages',
    'goto_page',
    'identify_current_page',
    'neighbors',
    'register_default_pages',
    'register_page',
]
