"""导航图、路径查找和按域拆分的导航边。"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.graph.combat import COMBAT_EDGES
from autowsgr.application.ui.navigation.graph.common import COMMON_EDGES, NavEdge
from autowsgr.application.ui.navigation.graph.logistics import LOGISTICS_EDGES


if TYPE_CHECKING:
    from autowsgr.common.types import PageName


NAV_GRAPH: tuple[NavEdge, ...] = (*COMMON_EDGES, *COMBAT_EDGES, *LOGISTICS_EDGES)
"""完整导航图；边按公共、战斗、后勤域合并。"""

_adjacency: dict[PageName, list[NavEdge]] = {}
for _edge in NAV_GRAPH:
    _adjacency.setdefault(_edge.source, []).append(_edge)


def find_path(source: str, target: str) -> list[NavEdge] | None:
    """查找从 *source* 到 *target* 的最短路径。"""
    if source == target:
        return []

    visited: set[str] = {source}
    queue: deque[tuple[str, list[NavEdge]]] = deque([(source, [])])
    while queue:
        current, path = queue.popleft()
        for edge in _adjacency.get(current, []):
            if edge.target in visited:
                continue
            new_path = [*path, edge]
            if edge.target == target:
                return new_path
            visited.add(edge.target)
            queue.append((edge.target, new_path))
    return None


def neighbors(page: str) -> set[str]:
    """返回 *page* 一步可到达的页面。"""
    return {str(edge.target.value) for edge in _adjacency.get(page, [])}


__all__ = [
    'COMBAT_EDGES',
    'COMMON_EDGES',
    'LOGISTICS_EDGES',
    'NAV_GRAPH',
    'NavEdge',
    'find_path',
    'neighbors',
]
