"""把三个业务域的导航边合成一张图，并负责路径查询。

`autowsgr.application.ui.navigation_old.service.py` 用 `find_path` 决定下一跳，
`autowsgr.application.ui.navigation_old.stack.py` 用 `neighbors` 缩小页面识别范围。
本文件读取 `graph/common.py`、`graph/combat.py`、`graph/logistics.py` 的边集合，
只做路径计算，不识别页面也不点击设备。
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation_old.graph.combat import COMBAT_EDGES
from autowsgr.application.ui.navigation_old.graph.common import COMMON_EDGES, NavEdge
from autowsgr.application.ui.navigation_old.graph.logistics import LOGISTICS_EDGES


if TYPE_CHECKING:
    from autowsgr.common.types import PageName


# ── 导航图汇总 ─────────────────────────────────────────────────

NAV_GRAPH: tuple[NavEdge, ...] = (*COMMON_EDGES, *COMBAT_EDGES, *LOGISTICS_EDGES)
"""完整导航图；边按公共、战斗、后勤域合并。"""

_adjacency: dict[PageName, list[NavEdge]] = {}
for _edge in NAV_GRAPH:
    _adjacency.setdefault(_edge.source, []).append(_edge)


# ── 路径查询 ─────────────────────────────────────────────────


def find_path(source: str, target: str) -> list[NavEdge] | None:
    """在 `_adjacency` 中查找从 *source* 到 *target* 的最短路径。"""
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
    """返回 `page` 在 `NAV_GRAPH` 中一步可到达的页面。"""
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
