"""模块功能：登记和查询页面间的导航动作。

上层调用：application.ui.navigation：读取已登记的跳转关系。

下层依赖：
- application.ui.navigation.types：提供页面名称。
- application.ui.navigation.page_checker：提供目标页面 checker。

边界：只保存和查询直接跳转关系，不计算路径或执行页面动作。
"""

from __future__ import annotations

from collections.abc import Callable

from autowsgr.application.ui.navigation.page_checker.home_checker import check_home_page
from autowsgr.application.ui.navigation.page_checker.sortie_checker import check_sortie_page
from autowsgr.application.ui.navigation.types import PageName


RouteEntry = tuple[str, PageName, PageName, str, Callable[..., bool]]
RoutePath = tuple[str, tuple[PageName, ...]]


class RouteManage:
    """登记并查询页面之间的导航动作。"""

    _routes: tuple[RouteEntry, ...] = (
        ('主页 → 出征页', PageName.HOME, PageName.SORTIE_MAP, 'navigate_to', check_sortie_page),
        ('出征页 → 主页', PageName.SORTIE_MAP, PageName.HOME, 'go_back', check_home_page),
    )
    _routes_by_edge = {(route[1], route[2]): route for route in _routes}

    @classmethod
    def get_paths(cls) -> tuple[RoutePath, ...]:
        """返回所有已登记的直接跳转边。"""
        return tuple(
            (description, (source, destination))
            for description, source, destination, _, _ in cls._routes
        )

    @classmethod
    def get_route_methods(cls, path: tuple[PageName, ...]) -> tuple[RouteEntry, ...]:
        """根据页面序列返回对应的路由动作。

        Args:
            path: 从起点到终点的页面序列。

        Returns:
            逐步路由记录；任一步未登记时返回空元组。
        """
        if len(path) < 2:
            return ()

        methods: list[RouteEntry] = []
        for source, destination in zip(path, path[1:]):
            route = cls._routes_by_edge.get((source, destination))
            if route is None:
                return ()
            methods.append(route)
        return tuple(methods)


__all__ = ['RouteManage']
