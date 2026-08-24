"""像素签名分类 — 页面/状态识别的坐标+颜色组合 (不易更改的静态事实)。

数据源: 本目录 YAML, 文件名 = 页面名。条目直接喂给
:meth:`PixelSignature.from_dict` (vision 层原生支持 YAML 数据化)::

    page:
      name: 主页面
      strategy: all
      rules:
        - {x: 0.6453, y: 0.9375, color: [52, 115, 168], tolerance: 30.0}

使用方式::

    from autowsgr.infra.base.constants.signatures import signature

    sig = signature('main', 'page')   # PixelSignature 实例
"""

from __future__ import annotations

from autowsgr.infra.base.constants._yaml import get
from autowsgr.vision import PixelSignature


def signature(page: str, key: str) -> PixelSignature:
    """取像素签名 (PixelSignature 实例, 由 YAML dict 构造)。"""
    return PixelSignature.from_dict(get('signatures', page, key))
