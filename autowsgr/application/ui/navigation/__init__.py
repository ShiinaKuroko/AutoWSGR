"""提供 UI 语义导航的分层公开入口。

业务执行器调用 `goto_page`；E2E 和调试工具读取页面识别结果；pytest 检查导航图、
注册表和页面栈。实现依赖同包的 service、recognition、registry、graph、stack，以及
下层页面控制器和 common 类型，不直接承载业务规则。
"""

from autowsgr.application.ui.navigation.graph import NAV_GRAPH, NavEdge, find_path, neighbors
from autowsgr.application.ui.navigation.recognition import get_current_page, identify_current_page
from autowsgr.application.ui.navigation.registry import (
    get_registered_pages,
    register_default_pages,
    register_page,
)
from autowsgr.application.ui.navigation.service import goto_page
from autowsgr.application.ui.navigation.stack import UIStack


__all__ = [
    # -- pytest 入口 ------------
    'NAV_GRAPH',
    'NavEdge',
    'UIStack',
    'find_path',
    # -- 工具入口 ------------
    'get_current_page',
    # -- pytest 入口 ------------
    'get_registered_pages',
    # -- 业务入口 ------------
    'goto_page',
    # -- 工具入口 ------------
    'identify_current_page',
    # -- pytest 入口 ------------
    'neighbors',
    'register_default_pages',
    'register_page',
]
