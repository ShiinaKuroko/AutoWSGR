"""UI 语义导航公开入口。

页面控制器和视觉识别器属于下层实现；业务只请求目标页面或安全锚点，
由这里的导航服务负责识别、寻路和交接。

业务层入口只有 ``goto_page``；E2E/调试使用页面识别接口；pytest 使用图、
注册表和页面栈接口。
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
    # pytest 入口：测试直接检查图、注册表和页面栈。
    'NAV_GRAPH',
    'NavEdge',
    'UIStack',
    'find_path',
    # 工具入口：E2E 和调试工具读取当前页面。
    'get_current_page',
    # pytest 入口：测试查询已注册页面。
    'get_registered_pages',
    # 业务入口：业务层只调用语义导航。
    'goto_page',
    # 工具入口：E2E 和调试工具读取当前页面。
    'identify_current_page',
    # pytest 入口：测试检查图和注册表。
    'neighbors',
    'register_default_pages',
    'register_page',
]
