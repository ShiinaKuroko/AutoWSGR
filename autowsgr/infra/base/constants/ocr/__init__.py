"""OCR / 识别参数分类 — 裁切区域、扫描步长、聚类阈值等静态参数。

数据源: 本目录 YAML, 文件名 = 页面名。值原样返回 (列表/字典/数字),
调用方按需构造类型 (如 ``ROI.from_tuple``)。

使用方式::

    from autowsgr.infra.base.constants.ocr import param

    roi = param('mission', 'button_scan_roi')   # [0.86, 0.17, 0.96, 0.85]
"""

from __future__ import annotations

from typing import Any

from autowsgr.infra.base.constants._yaml import get


def param(page: str, key: str) -> Any:
    """取 OCR / 识别参数 (原样返回)。"""
    return get('ocr', page, key)
