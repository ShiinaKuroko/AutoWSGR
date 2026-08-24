"""点击坐标包 — 数据源为同目录 YAML 文件。

硬约束 (已与用户敲定):
    YAML 文件格式不可变 — 键 + ``[x, y]`` 1280x720 绝对像素 + 简短注释。
    本加载器只负责读取与归一化 (绝对像素 → 0-1 相对坐标),
    不向 YAML 添加任何元数据 (color/tolerance/流程定义等)。

坐标应对未来 UI 改版: 游戏 UI 更新时直接修改 YAML 文件即可,
无需改动代码; 代码侧一律通过键名引用 (如 ``point('login', 'enter_game')``)。

使用方式::

    from autowsgr.infra.base.constants.coordinates import point

    x, y = point('login', 'enter_game')       # (0.891, 0.858) 相对坐标
    x, y = point('login', 'servers.hood')     # 嵌套键用点号路径
    ctrl.click(x, y)                          # ctrl.click 接受相对坐标

    probes = points('login', 'enter_servers')  # [[x, y], ...] → 归一化坐标列表
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# ═══════════════════════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════════════════════

_BASE_WIDTH = 1280
"""坐标采集基准分辨率宽 (像素)。"""

_BASE_HEIGHT = 720
"""坐标采集基准分辨率高 (像素)。"""

_DIR = Path(__file__).parent
"""YAML 文件所在目录 (与本加载器同目录)。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 加载
# ═══════════════════════════════════════════════════════════════════════════════


@lru_cache(maxsize=1)
def _load_all() -> dict[str, dict[str, Any]]:
    """加载全部坐标 YAML, 按文件名 (= 页面名) 分组。

    进程内只加载一次 (坐标是静态事实, 无需热更新)。
    """
    pages: dict[str, dict[str, Any]] = {}
    for file in sorted(_DIR.glob('*.yaml')):
        with file.open(encoding='utf-8') as fh:
            pages[file.stem] = yaml.safe_load(fh) or {}
    return pages


# ═══════════════════════════════════════════════════════════════════════════════
# 查询
# ═══════════════════════════════════════════════════════════════════════════════


def _resolve(page: str, key: str) -> Any:
    """沿点号路径下钻取 YAML 节点 (页面文件/键不存在时抛 KeyError)。"""
    pages = _load_all()
    if page not in pages:
        msg = f'坐标文件不存在: {page}.yaml (查找目录: {_DIR})'
        raise KeyError(msg)

    node: Any = pages[page]
    for part in key.split('.'):
        if not isinstance(node, dict) or part not in node:
            msg = f'坐标键不存在: {page}.{key}'
            raise KeyError(msg)
        node = node[part]
    return node


def _normalize(x: Any, y: Any) -> tuple[float, float]:
    """绝对像素 → 0-1 相对坐标。"""
    return (float(x) / _BASE_WIDTH, float(y) / _BASE_HEIGHT)


def point(page: str, key: str) -> tuple[float, float]:
    """取归一化相对坐标。

    Parameters
    ----------
    page:
        页面名 (= YAML 文件名), 如 ``'login'`` / ``'main'`` / ``'common'``。
    key:
        坐标键, 支持点号嵌套路径, 如 ``'servers.hood'``。

    Returns
    -------
    tuple[float, float]
        ``(x, y)`` 相对坐标 (0-1), 供 ``ctrl.click(x, y)`` 直接使用。

    Raises
    ------
    KeyError
        页面文件不存在、坐标键不存在或值格式不是 ``[x, y]``。
    """
    node = _resolve(page, key)

    # 叶子必须是 [x, y] 二元组
    if not (isinstance(node, (list, tuple)) and len(node) == 2):
        msg = f'坐标值必须是 [x, y]: {page}.{key} = {node!r}'
        raise KeyError(msg)

    return _normalize(*node)


def points(page: str, key: str) -> list[tuple[float, float]]:
    """取一组归一化相对坐标。

    YAML 值为 ``[x, y]`` 对列表 (如多个探测点), 按原顺序返回归一化结果。

    Raises
    ------
    KeyError
        页面文件不存在、键不存在或值格式不是 ``[[x, y], ...]``。
    """
    node = _resolve(page, key)

    if not isinstance(node, list) or any(
        not (isinstance(p, (list, tuple)) and len(p) == 2) for p in node
    ):
        msg = f'坐标值必须是 [[x, y], ...]: {page}.{key} = {node!r}'
        raise KeyError(msg)

    return [_normalize(*p) for p in node]
