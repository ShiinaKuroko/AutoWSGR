"""提供从当前页面到业务入口的跨页面导航。

业务执行器调用 `autowsgr.application.ui.navigation.service.goto_page`；本文件组合
`autowsgr.application.ui.navigation.recognition` 的识别、
`autowsgr.application.ui.navigation.graph` 的路径查询、
`autowsgr.application.ui.navigation.stack` 的页面栈和
`autowsgr.application.ui.navigation.graph.*` 的页面动作。底层异常来自
`autowsgr.common.ui.interaction.NavigationError`，页面点击和到达检查由
`autowsgr.application.ui.controller` 及 `autowsgr.common` 完成。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation import recognition as _recognition
from autowsgr.application.ui.navigation.graph import find_path
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import NavigationError


if TYPE_CHECKING:
    from autowsgr.application.ui.context import UIContext as GameContext

# ── 功能入口 ─────────────────────────────────────────────────

_log = get_logger('business.navigate')


def goto_page(ctx: GameContext, target: str) -> None:
    """让游戏到达业务需要的目标页面；失败时重建页面栈再试一次。"""
    try:
        _goto_page(ctx, target)
    except NavigationError as e:
        # 1、记录失败并重新识别当前页面。
        _log.error('[Navigate] 导航失败: {}', e)
        resynced = _recognition._resync_stack(ctx)

        # 2、重建栈后重新确认页面，再执行一次导航。
        _log.info('[Navigate] 栈重建 (resync): {}, 执行一次重试', resynced or '识别失败')
        current_page = _recognition.identify_current_page(ctx)

        _log.info('[Navigate] 当前页面: {}, 执行一次重试', current_page)
        _goto_page(ctx, target)


def goto_bath_from_normal_sortie(ctx: GameContext) -> None:
    """从普通出征准备页返回普通地图后进入澡堂。

    Args:
        ctx: 当前游戏上下文。
    """
    from autowsgr.application.ui.controller.battle_preparation import BattlePreparationPage

    BattlePreparationPage(ctx).go_back()
    goto_page(ctx, PageName.BATH)


def goto_bath_from_event_sortie(ctx: GameContext) -> None:
    """从活动出征准备页返回活动地图后进入澡堂。"""
    from autowsgr.application.ui.controller.battle_preparation.constants import CLICK_BACK
    from autowsgr.application.ui.controller.home.event_page import BaseEventPage
    from autowsgr.common.ui.interaction import click_and_wait_for_page

    click_and_wait_for_page(
        ctx.ctrl,
        click_coord=CLICK_BACK,
        checker=BaseEventPage.check_current_page,
        source=PageName.BATTLE_PREP,
        target=PageName.EVENT_MAP,
    )
    goto_page(ctx, PageName.BATH)


def goto_bath_from_campaign_sortie(ctx: GameContext) -> None:
    """从战役编队页经战役选择和主页进入澡堂。

    战役选择与普通地图共用 ``MapPage``，但这里显式执行两次回退，
    保留战役编队页 → 战役选择 → 主页 → 后院 → 澡堂的业务路径。

    Args:
        ctx: 当前游戏上下文。
    """
    from autowsgr.application.ui.controller.battle_preparation import (
        BattlePreparationPage,
    )
    from autowsgr.application.ui.controller.operations.sortie_page.battle_page import MapPage

    BattlePreparationPage(ctx).go_back()
    MapPage(ctx).go_back()
    goto_page(ctx, PageName.BATH)


def goto_bath_from_decisive_sortie(ctx: GameContext) -> None:
    """从决战出征准备页暂离保存后进入澡堂。

    决战地图不是普通页面注册项，必须先通过决战控制器返回决战地图，
    使用“暂离”保存进度，再确认回到决战总览页后继续既有澡堂路线。

    Args:
        ctx: 当前游戏上下文。
    """
    from autowsgr.application.ui.controller.operations.sortie_page.decisive_page import (
        DecisiveBattlePage,
        DecisiveMapController,
    )
    from autowsgr.common.system import DecisiveConfig
    from autowsgr.common.ui.interaction import wait_for_page

    config = getattr(ctx.config, 'decisive_battle', None) or DecisiveConfig()
    map_controller = DecisiveMapController(ctx, config)
    map_controller.go_to_map_page()
    map_controller.open_retreat_dialog()
    map_controller.confirm_leave()
    wait_for_page(
        ctx.ctrl,
        DecisiveBattlePage.check_current_page,
        source='决战暂离',
        target=PageName.DECISIVE_BATTLE,
    )
    goto_page(ctx, PageName.BATH)


# ── 导航实现 ─────────────────────────────────────────────────


def _goto_page(ctx: GameContext, target: str) -> None:
    """从当前页面开始逐步找到目标页面并执行页面动作。"""
    max_steps = 20
    stack = ctx.ui_stack
    # 第一次不知道当前页面，先检查全部页面；确认后只检查当前页面附近的候选。
    candidates: set[str] | None = None

    for step in range(max_steps):
        # 1、识别当前页面，并与页面栈对账。
        current = _recognition.identify_current_page(ctx, candidates=candidates)
        if current is None:
            raise NavigationError(
                f'无法识别当前页面，导航中止 (目标: {target})',
                screen=ctx.ctrl.screenshot(),
            )
        stack.observe(current)
        _recognition._sync_ctx_page(ctx, current)

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
