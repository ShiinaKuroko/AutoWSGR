"""提供从当前页面到业务入口的跨页面导航。

业务执行器调用 `goto_page`；它组合页面识别、导航图和页面控制器动作，并使用页面栈
记录来路。本文件依赖 `recognition`、`graph`、`UIStack` 和通用导航异常，不实现页面内业务。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.graph import find_path
from autowsgr.application.ui.navigation.recognition import (
    _resync_stack,
    _sync_ctx_page,
    identify_current_page,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.ui.interaction import NavigationError


if TYPE_CHECKING:
    from autowsgr.application.ui.context import UIContext as GameContext

# -- 功能入口 ------------

_log = get_logger('business.navigate')


def goto_page(ctx: GameContext, target: str) -> None:
    """到达目标页面；首次失败时重建页面栈并重试一次。"""
    try:
        _goto_page(ctx, target)
    except NavigationError as e:
        # 1、记录失败并重新识别当前页面。
        _log.error('[Navigate] 导航失败: {}', e)
        resynced = _resync_stack(ctx)

        # 2、重建栈后重新确认页面，再执行一次导航。
        _log.info('[Navigate] 栈重建 (resync): {}, 执行一次重试', resynced or '识别失败')
        current_page = identify_current_page(ctx)

        _log.info('[Navigate] 当前页面: {}, 执行一次重试', current_page)
        _goto_page(ctx, target)


# -- 导航实现 ------------


def _goto_page(ctx: GameContext, target: str) -> None:
    """按当前页面逐步重规划，直到到达目标或抛出导航异常。"""
    max_steps = 20
    stack = ctx.ui_stack
    # 候选集:首轮全表扫描(真不知在哪);每步由栈给出
    # {current} + neighbors(current) + {parent} + {target} + neighbors(target),
    # 相比纯邻域机制多纳入 parent, 覆盖回退时序与无入边叶子页 (CHOOSE_SHIP 等)。
    candidates: set[str] | None = None

    for step in range(max_steps):
        # 1、识别当前页面，并与页面栈对账。
        current = identify_current_page(ctx, candidates=candidates)
        if current is None:
            raise NavigationError(
                f'无法识别当前页面，导航中止 (目标: {target})',
                screen=ctx.ctrl.screenshot(),
            )
        stack.observe(current)
        _sync_ctx_page(ctx, current)

        # 2、已经在目标页面时结束本次导航。
        if current == target:
            _log.info('[Navigate] 已在目标页面: {}', target)
            return

        # 3、查找下一步路径，找不到时立即终止。
        path = find_path(current, target)
        if path is None:
            raise NavigationError(
                f"无法找到从 '{current}' 到 '{target}' 的路径",
                screen=ctx.ctrl.screenshot(),
            )

        if not path:  # Should be covered by current == target, but safe check
            _log.info('[Navigate] 已在目标页面: {}', target)
            return

        # 4、先声明下一页，再执行点击；下一轮识别会校正栈。
        edge = path[0]
        _log.debug(
            '[Navigate] 步骤 {} (总限 {}): {} → {} ({})',
            step + 1,
            max_steps,
            edge.source,
            edge.target,
            edge.description,
        )
        stack.push(edge.target)
        edge.action(ctx)
        candidates = stack.candidates(target) or None

    raise NavigationError(
        f'导航步数超限 ({max_steps})，目标: {target}',
        screen=ctx.ctrl.screenshot(),
    )
