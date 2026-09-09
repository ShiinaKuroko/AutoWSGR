"""从截图识别当前页面，并把结果同步给运行时上下文。

`autowsgr.application.ui.navigation.service._goto_page` 调用
`identify_current_page`，E2E 和调试工具调用 `get_current_page`。本文件依赖
`autowsgr.application.ui.navigation.registry` 的 `_PAGE_REGISTRY` 和 `_OVERLAY_PAGES`，
`autowsgr.common.vision.page_match.PageMatch`、`autowsgr.common.types.PageName`、
`autowsgr.common.system.logger.get_logger` 及 `autowsgr.application.ui.context.UIContext.ctrl`；
不执行点击。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation import registry as _registry
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.vision.page_match import PageMatch


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext


# ── 识别配置 ─────────────────────────────────────────────────

_log = get_logger('business.navigate')

MAX_IDENTIFY_ATTEMPTS: int = 5
"""页面识别最大尝试次数。"""

IDENTIFY_INTERVAL: float = 1.0
"""页面识别重试间隔 (秒)。"""


# ── 截图识别 ─────────────────────────────────────────────────


def get_current_page(
    screen: np.ndarray,
    candidates: set[str] | None = None,
) -> str | None:
    """调用注册表检查器，根据截图返回当前页面名。"""
    # 1、只检查调用方允许的已注册页面。
    registered = list(_registry._PAGE_REGISTRY)
    names = [name for name in registered if candidates is None or name in candidates]
    hits: list[PageMatch] = []
    failed: list[str] = []

    for name in names:
        checker = _registry._PAGE_REGISTRY[name]
        try:
            result = _normalize_match(name, checker(screen))
        except Exception:
            _log.opt(exception=True).warning("[UI] 页面 '{}' 识别器异常", name)
            failed.append(name)
            continue
        if result.matched:
            hits.append(result)

    # 2、覆盖层优先，再按匹配强度选择页面。
    if hits:
        overlay_hits = [result for result in hits if result.name in _registry._OVERLAY_PAGES]
        pool = overlay_hits or hits
        pool.sort(key=lambda result: result.score, reverse=True)
        best = pool[0]
        _log.debug(
            '[UI] 当前页面: {} (score={:.3f}, 候选 {} / 命中 {})',
            best.name,
            best.score,
            len(names),
            len(hits),
        )
        return best.name

    # 3、没有命中时记录原因，把重试交给上层。
    if failed:
        _log.warning(
            '[UI] 无匹配页面，且以下识别器抛异常: {} (评估 {} 个候选)',
            failed,
            len(names),
        )
    else:
        _log.debug('[UI] 当前页面: 无匹配 (评估 {} 个候选)', len(names))
    return None


def identify_current_page(
    ctx: GameContext,
    candidates: set[str] | None = None,
) -> str | None:
    """调用 `get_current_page` 重试识别 `UIContext.ctrl.screenshot` 的当前页面。"""
    # 1、确保默认页面检查器已经注册。
    _registry.register_default_pages()
    ctrl = ctx.ctrl
    # 2、在页面动画期间重复截图识别。
    for attempt in range(MAX_IDENTIFY_ATTEMPTS):
        screen = ctrl.screenshot()
        page = get_current_page(screen, candidates=candidates)
        if page is not None:
            return page
        _log.debug('[Navigate] 页面识别失败 (第 {} 次尝试), 等待重试', attempt + 1)
        time.sleep(IDENTIFY_INTERVAL)

    # 3、候选集耗尽后做一次全量识别，避免栈漂移卡住导航。
    if candidates is not None:
        page = get_current_page(ctrl.screenshot())
        if page is not None:
            _log.warning('[Navigate] 候选识别失败, 全量兜底命中: {}', page)
            return page
    return None


# ── 内部同步 ─────────────────────────────────────────────────


def _normalize_match(name: str, result: object) -> PageMatch:
    """校验识别器结果并统一为 `autowsgr.common.vision.page_match.PageMatch`。"""
    if not isinstance(result, PageMatch):
        raise TypeError(f'页面识别器 {name!r} 必须返回 PageMatch')
    if result.name == name:
        return result
    return PageMatch(name=name, matched=result.matched, score=result.score)


def _resync_stack(ctx: GameContext) -> str | None:
    """用当前截图重建 `autowsgr.application.ui.navigation.stack.UIStack`。"""
    screen = ctx.ctrl.screenshot()
    identified = get_current_page(screen)
    if identified is None:
        ctx.ui_stack.clear()
        _log.warning('[UIStack] 全量识别失败, 栈已清空')
        return None
    ctx.ui_stack.reset(identified, screen=screen)
    _log.info('[UIStack] 栈重建为 [{}]', identified)
    return identified


def _sync_ctx_page(ctx: GameContext, name: str) -> None:
    """把结果写入 `autowsgr.application.ui.context.UIContext.current_page`。"""
    try:
        ctx.current_page = PageName(name)
    except ValueError:
        ctx.current_page = None


__all__ = ['get_current_page', 'identify_current_page']
