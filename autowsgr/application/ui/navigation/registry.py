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

# 登录页与区服选择页的确认节奏：点击后要等弹层动画，单帧会立刻判失败。
_LOGIN_PAGE_CONFIRM_ATTEMPTS = 10
_SERVER_SELECT_CONFIRM_ATTEMPTS = 10
_LOGIN_PAGE_CONFIRM_INTERVAL_SECONDS = 0.5


def _is_login_page(ctx: ContextHandle, **kwargs: object) -> bool:
    """确认登录页；点开弹层后画面要等一会儿才切过去。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        **kwargs: 透传前后识别参数（absent / attempts / interval_seconds）。

    Returns:
        断言满足时为真。
    """
    return login_checker.check_login_page(
        ctx,
        absent=bool(kwargs.get('absent', False)),
        attempts=int(kwargs.get('attempts', _LOGIN_PAGE_CONFIRM_ATTEMPTS)),
        interval_seconds=float(
            kwargs.get('interval_seconds', _LOGIN_PAGE_CONFIRM_INTERVAL_SECONDS)
        ),
    )


def _is_server_select(ctx: ContextHandle, **kwargs: object) -> bool:
    """确认区服选择页；打开区服列表后弹层动画要等一会儿。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        **kwargs: 透传前后识别参数（absent / attempts / interval_seconds）。

    Returns:
        断言满足时为真。
    """
    return login_checker.check_server_select(
        ctx,
        absent=bool(kwargs.get('absent', False)),
        attempts=int(kwargs.get('attempts', _SERVER_SELECT_CONFIRM_ATTEMPTS)),
        interval_seconds=float(
            kwargs.get('interval_seconds', _LOGIN_PAGE_CONFIRM_INTERVAL_SECONDS)
        ),
    )


def _is_event_map(ctx: ContextHandle, **kwargs: object) -> bool:
    """确认活动地图页身份。

    只判"这一页是不是活动地图"，不校验任务玩法，因此在没有活动任务的导航里也能参与定位。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        **kwargs: 透传前后识别参数（absent / attempts / interval_seconds）。

    Returns:
        断言满足时为真。
    """
    return stage_push.check_event_map_page(ctx, **kwargs)  # type: ignore[arg-type]


def _is_event_stage_overlay(ctx: ContextHandle, **kwargs: object) -> bool:
    """确认活动章节浮窗的出现或消失。

    只判"浮窗在不在"，不校验它指向哪个章节：定位当前页时任务的章节参数未必就是眼前这个浮窗，
    章节是否点对由业务与 E2E 用 ``check_event_sortie_prepare(ctx, stage=...)`` 单独校验。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        **kwargs: 透传前后识别参数（absent / attempts / interval_seconds）。

    Returns:
        断言满足时为真。
    """
    return stage_push.check_event_sortie_prepare(ctx, **kwargs)  # type: ignore[arg-type]


# 值统一收 (ctx, *, absent=False, attempts=1, interval_seconds=0.5)：前识别判出现，
# 后识别（absent=True）判消失，节奏由各页面自己带。
_PAGE_CHECKERS: dict[PageName, Callable[..., bool]] = {
    PageName.LOGIN_PAGE: _is_login_page,
    PageName.SERVER_SELECT: _is_server_select,
    PageName.HOME: lambda ctx, **kwargs: home_checker.check_home_page(
        ctx,
        absent=bool(kwargs.get('absent', False)),
        attempts=int(kwargs.get('attempts', _HOME_CONFIRM_ATTEMPTS)),
        interval_seconds=float(kwargs.get('interval_seconds', _HOME_CONFIRM_INTERVAL_SECONDS)),
    ),
    PageName.SORTIE_MAP: sortie_checker.check_sortie_page,
    PageName.EVENT_MAP: _is_event_map,
    PageName.EVENT_STAGE_OVERLAY: _is_event_stage_overlay,
}


# ── 页面 → 可达列表 ─────────────────────────────────────────────────────────

_NAV_TARGETS: dict[PageName, tuple[NavTarget, ...]] = {
    PageName.LOGIN_PAGE: (
        NavTarget(
            PageName.SERVER_SELECT,
            lambda ctx, **_: LoginPage(ctx).click_switch_entry(
                login_checker.read_switch_entry_center(ctx)
            ),
            '登录页 → 区服选择页',
        ),
        NavTarget(
            PageName.HOME,
            lambda ctx, **_: LoginPage(ctx).click_enter_game(
                login_checker.read_enter_button_center(ctx)
            ),
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
    PageName.EVENT_STAGE_OVERLAY: (
        NavTarget(
            PageName.EVENT_MAP,
            lambda ctx, **_: EventPage(ctx, event_type=_event_type(ctx)).click_overlay_close(),
            '活动章节浮窗 → 活动地图',
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
