"""颜色常量分类 — 游戏界面颜色与容差 (不易更改的静态事实)。

数据源: 本目录 YAML, 文件名 = 页面名。条目格式::

    notification_red: {rgb: [255, 89, 45], tolerance: 40.0}

纯颜色阈值 (非 Color 对象, 如 RGB 分量比较) 用 :func:`param` 原样取。

使用方式::

    from autowsgr.infra.base.constants.colors import color, tolerance

    c = color('main', 'notification_red')      # Color 实例
    tol = tolerance('main', 'notification_red')  # float
"""

from __future__ import annotations

from typing import Any

from autowsgr.infra.base.constants._yaml import get
from autowsgr.vision import Color


def color(page: str, key: str) -> Color:
    """取 {rgb, tolerance} 条目中的颜色 (Color 实例)。"""
    data = get('colors', page, key)
    return Color.of(*data['rgb'])  # type: ignore[arg-type]


def tolerance(page: str, key: str) -> float:
    """取 {rgb, tolerance} 条目中的容差 (缺省 0.0)。"""
    data = get('colors', page, key)
    return float(data.get('tolerance', 0.0))


def param(page: str, key: str) -> Any:
    """原样取颜色分类下的任意值 (阈值等非 Color 条目)。"""
    return get('colors', page, key)
