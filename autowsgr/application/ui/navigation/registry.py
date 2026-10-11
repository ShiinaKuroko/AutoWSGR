"""模块功能：维护页面之间的可达列表与到达确认。

上层调用：
- application.ui.navigation.service：查询可达目标、到达确认与完整路径。

下层依赖：
- navigation.types：提供页面契约与错误。
- navigation.page_checker：提供到达确认入口。
- application.ui.controller：提供一次点击的动作。

边界：只维护"能去哪、怎么去、到了吗"，不截图、不点击、不判断业务状态。
每条边就是一行数据，不为边写转发函数。
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home.event_page import EventPage
from autowsgr.application.ui.controller.home.main_page import HomePage, Target
from autowsgr.application.ui.controller.login import LoginPage
from autowsgr.application.ui.controller.operations.sortie_page.main_page import SortiePage
from autowsgr.application.ui.navigation.page_checker import (
    home_checker,
    login_checker,
    sortie_checker,
)
from autowsgr.application.ui.navigation.page_checker.event_checker import stage_push
from autowsgr.application.ui.navigation.types import NavigationError, NavTarget, PageName


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.dispatch.context import ContextHandle


# ── 页面 → 到达确认 ─────────────────────────────────────────────────────────

# 主页确认节奏：从登录页进入要等登录动画与加载，因此给足重试。
_HOME_CONFIRM_ATTEMPTS = 30
_HOME_CONFIRM_INTERVAL_SECONDS = 1.0

_PAGE_CHECKERS: dict[PageName, Callable[[ContextHandle], bool]] = {
    PageName.LOGIN_PAGE: login_checker.check_login_page,
    PageName.SERVER_SELECT: login_checker.check_server_select,
    PageName.HOME: lambda ctx: home_checker.check_home_page(
        ctx,
        attempts=_HOME_CONFIRM_ATTEMPTS,
        interval_seconds=_HOME_CONFIRM_INTERVAL_SECONDS,
    ),
    PageName.SORTIE_MAP: sortie_checker.check_sortie_page,
    PageName.EVENT_MAP: lambda ctx: stage_push.check_event_map_page(
        ctx,
        event_type=_event_type(ctx),
    ),
    PageName.EVENT_STAGE_OVERLAY: lambda ctx: stage_push.check_event_sortie_prepare(
        ctx,
        event_type=_event_type(ctx),
        stage=_event_stage(ctx),
    ),
}


# ── 页面 → 可达列表 ─────────────────────────────────────────────────────────

_NAV_TARGETS: dict[PageName, tuple[NavTarget, ...]] = {
    PageName.LOGIN_PAGE: (
        NavTarget(
            PageName.SERVER_SELECT,
            lambda ctx, **_: LoginPage(ctx).click_switch_entry(),
            '登录页 → 区服选择页',
        ),
        NavTarget(
            PageName.HOME,
            lambda ctx, **_: LoginPage(ctx).click_enter_game(),
            '登录页 → 主页',
        ),
    ),
    PageName.SERVER_SELECT: (
        NavTarget(
            PageName.LOGIN_PAGE,
            lambda ctx, **params: LoginPage(ctx).click_server(int(params['position'])),
            '区服选择页 → 登录页',
        ),
    ),
    PageName.HOME: (
        NavTarget(
            PageName.SORTIE_MAP,
            lambda ctx, **_: HomePage(ctx).go_to(Target.SORTIE),
            '首页 → 出征页',
        ),
        NavTarget(
            PageName.EVENT_MAP,
            lambda ctx, **_: HomePage(ctx).go_to(Target.EVENT),
            '首页 → 活动地图',
        ),
    ),
    PageName.SORTIE_MAP: (
        NavTarget(
            PageName.HOME,
            lambda ctx, **_: SortiePage(ctx).go_back(),
            '出征页 → 首页',
        ),
    ),
    PageName.EVENT_MAP: (
        NavTarget(
            PageName.EVENT_STAGE_OVERLAY,
            lambda ctx, **params: EventPage(ctx, event_type=_event_type(ctx)).go_to_overlay(
                int(params['node'])
                if 'node' in params
                else stage_push.parse_stage(_event_stage(ctx)).node
            ),
            '活动地图 → 章节浮窗',
        ),
        NavTarget(
            PageName.HOME,
            lambda ctx, **_: EventPage(ctx, event_type=_event_type(ctx)).go_back(),
            '活动地图 → 首页',
        ),
    ),
}


# ── 上下文辅助 ──────────────────────────────────────────────────────────────


def _event_type(ctx: ContextHandle) -> str:
    """读取任务绑定的活动玩法标识。

    Raises:
        NavigationError: 任务没有绑定活动玩法。
    """
    event_type = ctx.read_event_type()
    if event_type is None:
        raise NavigationError('活动导航需要任务绑定 event_type')
    return event_type


def _event_stage(ctx: ContextHandle) -> str:
    """读取任务绑定的活动章节标识。

    Raises:
        NavigationError: 任务没有绑定活动章节。
    """
    stage = ctx.read_event_stage()
    if stage is None:
        raise NavigationError('活动导航需要任务绑定 event_stage')
    return stage


# ── 查询入口 ────────────────────────────────────────────────────────────────


def get_targets(page: PageName) -> tuple[NavTarget, ...]:
    """返回某个页面可以直达的目标。"""
    return _NAV_TARGETS.get(page, ())


def get_checker(page: PageName) -> Callable[[ContextHandle], bool] | None:
    """返回某个页面的到达确认入口。"""
    return _PAGE_CHECKERS.get(page)


def find_path(source: PageName, target: PageName) -> tuple[NavTarget, ...]:
    """在可达列表上广度拼接出从 source 到 target 的路径。

    Args:
        source: 起点页面。
        target: 目标页面。

    Returns:
        依次执行的边；起点即目标时返回空元组。

    Raises:
        NavigationError: 没有可达路径。
    """
    if source == target:
        return ()

    queue: deque[tuple[PageName, tuple[NavTarget, ...]]] = deque([(source, ())])
    visited = {source}
    while queue:
        page, path = queue.popleft()
        for edge in get_targets(page):
            if edge.target in visited:
                continue
            next_path = (*path, edge)
            if edge.target == target:
                return next_path
            visited.add(edge.target)
            queue.append((edge.target, next_path))
    raise NavigationError(f'没有从 {source.value!r} 到 {target.value!r} 的可达路径')


__all__ = ['find_path', 'get_checker', 'get_targets']
