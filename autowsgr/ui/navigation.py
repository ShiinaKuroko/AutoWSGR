"""兼容 shim — 实现已迁移至 :mod:`autowsgr.infra.ui.navigation.graph`。

老代码仍可 ``from autowsgr.infra.ui.navigation.graph import find_path``，
新代码请直接使用新路径。
"""

from autowsgr.infra.ui.navigation.graph import (
    NAV_GRAPH,
    NavEdge,
    find_path,
    neighbors,
)


__all__ = [
    'NAV_GRAPH',
    'NavEdge',
    'find_path',
    'neighbors',
]
