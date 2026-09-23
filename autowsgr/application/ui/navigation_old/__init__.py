"""导航器的公开入口。

业务执行器调用 `autowsgr.application.ui.navigation_old.service.py` 的 `goto_page`；
E2E 和调试工具读取 `autowsgr.application.ui.navigation_old.recognition.py` 的识别结果；
pytest 检查 `graph/`、`registry.py` 和 `stack.py`。本文件只做公开导入，实际导航由
同目录模块完成，页面操作继续由 `autowsgr.application.ui.controller` 和 `autowsgr.common`
提供。
"""

from autowsgr.application.ui.navigation_old.graph import NAV_GRAPH, NavEdge, find_path, neighbors
from autowsgr.application.ui.navigation_old.recognition import get_current_page, identify_current_page
from autowsgr.application.ui.navigation_old.registry import (
    get_registered_pages,
    register_default_pages,
    register_page,
)
from autowsgr.application.ui.navigation_old.service import (
    goto_bath_from_campaign_sortie,
    goto_bath_from_decisive_sortie,
    goto_bath_from_event_sortie,
    goto_bath_from_normal_sortie,
    goto_page,
)
from autowsgr.application.ui.navigation_old.stack import UIStack


__all__ = [
    # ── pytest 入口 ─────────────────────────────────────────────────
    'NAV_GRAPH',
    'NavEdge',
    'UIStack',
    'find_path',
    # ── 工具入口 ─────────────────────────────────────────────────
    'get_current_page',
    # ── pytest 入口 ─────────────────────────────────────────────────
    'get_registered_pages',
    # ── 业务入口 ─────────────────────────────────────────────────
    'goto_bath_from_campaign_sortie',
    'goto_bath_from_decisive_sortie',
    'goto_bath_from_event_sortie',
    'goto_bath_from_normal_sortie',
    'goto_page',
    # ── 工具入口 ─────────────────────────────────────────────────
    'identify_current_page',
    # ── pytest 入口 ─────────────────────────────────────────────────
    'neighbors',
    'register_default_pages',
    'register_page',
]
