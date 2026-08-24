"""通用 YAML 常量加载器 — colors/ocr/signatures 分类共用。

与 coordinates/ 的差异: coordinates 的 ``point()`` 负责 1280x720 绝对像素 →
相对坐标的归一化; 本加载器只做「按分类目录加载全部 YAML (文件名 = 页面名)
+ 点号路径取值」, 不做任何数值变换, 值原样返回 (颜色/OCR 参数/签名结构)。

使用方式::

    from autowsgr.infra.base.constants._yaml import get

    value = get('colors', 'main', 'notification_red')   # {'rgb': [...], 'tolerance': 40.0}
    value = get('ocr', 'mission', 'button_scan_roi')    # [0.86, 0.17, 0.96, 0.85]
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


# 分类目录基址 (与 coordinates/ 同级的兄弟目录)
_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def _load(category: str) -> dict[str, dict[str, Any]]:
    """加载某分类目录下全部 YAML, 按文件名 (= 页面名) 分组。进程内只加载一次。"""
    pages: dict[str, dict[str, Any]] = {}
    category_dir = _DIR / category
    if not category_dir.is_dir():
        raise KeyError(f'常量分类目录不存在: {category_dir}')
    for file in sorted(category_dir.glob('*.yaml')):
        with file.open(encoding='utf-8') as fh:
            pages[file.stem] = yaml.safe_load(fh) or {}
    return pages


def get(category: str, page: str, key: str) -> Any:
    """取分类常量, 支持点号嵌套路径 (如 ``'claim.r_min'``)。

    Raises
    ------
    KeyError
        分类/页面文件不存在或键不存在。
    """
    pages = _load(category)
    if page not in pages:
        msg = f'常量文件不存在: {category}/{page}.yaml (查找目录: {_DIR / category})'
        raise KeyError(msg)
    node: Any = pages[page]
    for part in key.split('.'):
        if not isinstance(node, dict) or part not in node:
            msg = f'常量键不存在: {category}.{page}.{key}'
            raise KeyError(msg)
        node = node[part]
    return node
