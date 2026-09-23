"""决战控制器配置与地图数据。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from autowsgr.common.system.file_utils import load_yaml
from autowsgr.common.system.logger import get_logger


_log = get_logger('business.combat.decisive')


# ═══════════════════════════════════════════════════════════════════════════════
# 规范地图数据
# ═══════════════════════════════════════════════════════════════════════════════

_MAP_DATA_ROOT = (
    Path(__file__).resolve().parents[3]
    / 'common'
    / 'data'
    / 'map'
    / 'decisive_battle'
    / 'silent_warrior'
)


@lru_cache(maxsize=18)
def _load_map_data(chapter: int, stage: int) -> dict[str, Any]:
    """加载并校验一个决战小关的规范节点图。"""
    if not 1 <= chapter <= 6 or not 1 <= stage <= 3:
        raise ValueError(f'无效章节/小关: chapter={chapter}, stage={stage}')
    path = _MAP_DATA_ROOT / f'EX-{chapter}-{stage}.yaml'
    data = load_yaml(path)
    if not isinstance(data, dict) or not isinstance(data.get('nodes'), dict):
        raise TypeError(f'决战地图数据无效: {path}')
    return data


def _node_label(node_id: str, node: dict[str, Any]) -> str:
    """读取节点的无分支字母标签。"""
    return str(node.get('label', node_id)).upper()


def _leftmost_node_ids(data: dict[str, Any]) -> dict[str, str]:
    """返回始终选择第一条边时经过的节点 ID。"""
    nodes = data['nodes']
    result: dict[str, str] = {}
    current = '0'
    visited: set[str] = set()
    while current not in visited:
        visited.add(current)
        node = nodes.get(current)
        if not isinstance(node, dict):
            break
        label = _node_label(current, node)
        result.setdefault(label, current)
        next_nodes = node.get('next', [])
        if not next_nodes:
            break
        current = str(next_nodes[0])
    return result


class MapData:
    """按规范的每关节点图查询决战终点、关键点、敌方和路线。"""

    @staticmethod
    def get_stage_end_node(chapter: int, stage: int) -> str:
        """获取指定章节、小关的终止节点字母。

        Parameters
        ----------
        chapter:
            章节编号 (1-6)。
        stage:
            小关编号 (1-3)。

        Returns
        -------
        str
            终止节点字母 (如 ``'H'``, ``'J'``)。
            若地图数据不存在或终点不唯一，则抛出明确异常。
        """
        data = _load_map_data(chapter, stage)
        terminal_labels = {
            _node_label(node_id, node)
            for node_id, node in data['nodes'].items()
            if isinstance(node, dict) and node_id != '0' and not node.get('next', [])
        }
        if len(terminal_labels) != 1:
            raise ValueError(f'决战终点数据无效: chapter={chapter}, stage={stage}')
        return terminal_labels.pop()

    @staticmethod
    def is_stage_end(chapter: int, stage: int, node: str) -> bool:
        """判断当前节点是否为该小关的终止节点。

        Parameters
        ----------
        chapter:
            章节编号 (1-6)。
        stage:
            小关编号 (1-3)。
        node:
            当前节点字母 (如 ``'A'``, ``'H'``)。
        """
        return node.upper() == MapData.get_stage_end_node(chapter, stage)

    @staticmethod
    def get_key_points(chapter: int, stage: int) -> set[str]:
        """获取指定章节、小关的关键节点集合 (需夜战)。

        Parameters
        ----------
        chapter:
            章节编号 (4-6)。
        stage:
            小关编号 (1-3)。

        Returns
        -------
        set[str]
        关键节点字母集合。
        """
        data = _load_map_data(chapter, stage)
        return {str(node).upper() for node in data.get('key_points', [])}

    @staticmethod
    def is_key_point(chapter: int, stage: int, node: str) -> bool:
        """判断当前节点是否为关键点 (需夜战)。"""
        return node.upper() in MapData.get_key_points(chapter, stage)

    @staticmethod
    def get_enemy(chapter: int, stage: int, node: str) -> list[str]:
        """获取指定章节/小关/节点的敌方编成。"""
        data = _load_map_data(chapter, stage)
        enemy = data.get('enemy', {}).get(node.upper(), [])
        return [str(value) for value in enemy if value]

    @staticmethod
    def get_leftmost_choices(chapter: int, stage: int, source_node: str) -> list[str]:
        """获取始终选择左侧路线时，当前节点的后继节点 ID。"""
        data = _load_map_data(chapter, stage)
        nodes = data['nodes']
        source = source_node.upper()
        source_id = '0' if source in {'', 'U', '0'} else _leftmost_node_ids(data).get(source)
        if source_id is None:
            candidates = [
                (node.get('column', 0), node.get('index', 0), node_id)
                for node_id, node in nodes.items()
                if isinstance(node, dict) and _node_label(node_id, node) == source
            ]
            source_id = min(candidates)[2] if candidates else None
        if source_id is None:
            return []
        return [str(node_id) for node_id in nodes[source_id].get('next', [])]
