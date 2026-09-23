"""application/vision 校准数据的只读加载器。"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

import yaml

from autowsgr.common import vision


_DATA_ROOT = Path(__file__).resolve().parent / 'data'
_BASE_WIDTH = 1280
_BASE_HEIGHT = 720


@cache
def _load(category: str) -> dict[str, dict[str, Any]]:
    """加载一个校准分类下的全部页面 YAML。"""
    directory = _DATA_ROOT / category
    if not directory.is_dir():
        raise KeyError(f'校准分类目录不存在: {directory}')
    return {
        file.stem: yaml.safe_load(file.read_text(encoding='utf-8')) or {}
        for file in sorted(directory.glob('*.yaml'))
    }


def get(category: str, page: str, key: str) -> Any:
    """读取校准 YAML 中的点号路径值。"""
    pages = _load(category)
    if page not in pages:
        raise KeyError(f'校准页面不存在: {category}/{page}.yaml')
    value: Any = pages[page]
    for part in key.split('.'):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(f'校准键不存在: {category}.{page}.{key}')
        value = value[part]
    return value


def point(page: str, key: str) -> tuple[float, float]:
    """读取 1280x720 绝对坐标并归一化为相对坐标。"""
    value = get('coordinates', page, key)
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise KeyError(f'坐标值必须是 [x, y]: {page}.{key} = {value!r}')
    return float(value[0]) / _BASE_WIDTH, float(value[1]) / _BASE_HEIGHT


def points(page: str, key: str) -> list[tuple[float, float]]:
    """读取并归一化一组 1280x720 绝对坐标。"""
    value = get('coordinates', page, key)
    if not isinstance(value, list):
        raise KeyError(f'坐标值必须是 [[x, y], ...]: {page}.{key} = {value!r}')
    return [
        (float(item[0]) / _BASE_WIDTH, float(item[1]) / _BASE_HEIGHT)
        for item in value
        if isinstance(item, (list, tuple)) and len(item) == 2
    ]


def param(page: str, key: str) -> Any:
    """读取选定页面的 OCR 校准参数。"""
    return get('ocr', page, key)


def color(page: str, key: str) -> vision.Color:
    """读取颜色校准值。"""
    value = get('colors', page, key)
    return vision.Color.of(*value['rgb'])


def tolerance(page: str, key: str) -> float:
    """读取颜色容差。"""
    return float(get('colors', page, key).get('tolerance', 0.0))


def signature(page: str, key: str) -> vision.PixelSignature:
    """读取像素签名校准值。"""
    return vision.PixelSignature.from_dict(get('signatures', page, key))


__all__ = ['color', 'get', 'param', 'point', 'points', 'signature', 'tolerance']
