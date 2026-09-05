"""当前页面识别和上下文同步。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.registry import get_current_page, register_default_pages
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName


if TYPE_CHECKING:
    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('business.navigate')

MAX_IDENTIFY_ATTEMPTS: int = 5
"""页面识别最大尝试次数。"""

IDENTIFY_INTERVAL: float = 1.0
"""页面识别重试间隔 (秒)。"""


def identify_current_page(
    ctx: GameContext,
    candidates: set[str] | None = None,
) -> str | None:
    """截图并识别当前页面。

    尝试多次截图以应对动画或加载中的情况。候选集识别重试耗尽后
    追加一轮全量识别兜底 —— 栈漂移可能把真实页面排除在候选之外。

    Parameters
    ----------
    candidates:
        候选页面名集合。``None`` 时评估全部注册页;导航过程中由
        :func:`_goto_page` 从 :attr:`GameContext.ui_stack` 计算并传入,
        以收缩搜索空间。

    Returns
    -------
    str | None
        当前页面名称，无法识别返回 ``None``。
    """
    register_default_pages()
    ctrl = ctx.ctrl
    for attempt in range(MAX_IDENTIFY_ATTEMPTS):
        screen = ctrl.screenshot()
        page = get_current_page(screen, candidates=candidates)
        if page is not None:
            return page
        _log.debug(
            '[Navigate] 页面识别失败 (第 {} 次尝试), 等待重试',
            attempt + 1,
        )
        time.sleep(IDENTIFY_INTERVAL)

    if candidates is not None:
        # 候选耗尽:降级全量识别一轮(候选集可能因栈漂移漏掉真实页面)
        screen = ctrl.screenshot()
        page = get_current_page(screen)
        if page is not None:
            _log.warning('[Navigate] 候选识别失败, 全量兜底命中: {}', page)
            return page
    return None


def _sync_ctx_page(ctx: GameContext, name: str) -> None:
    """把识别结果同步到 ``ctx.current_page``。"""
    try:
        ctx.current_page = PageName(name)
    except ValueError:
        ctx.current_page = None


__all__ = ['identify_current_page']
