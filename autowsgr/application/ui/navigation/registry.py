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
from dataclasses import dataclass
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
from autowsgr.application.ui.navigation.types import NavigationError, PageName
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui.navigation')


# ── 每日浮窗动作 ─────────────────────────────────────────────────────────────

# 浮窗链的每一步都"先问再做"：不在就什么都不做，避免空点；到达确认由边自己关掉。


def _close_daily_news(ctx: ContextHandle, **_: object) -> None:
    """有每日公告就关掉，没有就什么都不做。

    未勾选「今日不再显示」时先勾上，避免第二天又弹。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
    """
    state = home_checker.check_home_news_overlay(ctx)
    if not state.matched:
        return
    page = HomePage(ctx)
    if state.checked is False:
        page.click_news_checkbox()
    page.click_news_close()


def _claim_daily_reward(ctx: ContextHandle, **_: object) -> None:
    """有每日奖励就领取，没有就什么都不做。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
    """
    if not home_checker.check_home_reward_overlay(ctx):
        return
    HomePage(ctx).click_reward_claim()


def _confirm_daily_reward(ctx: ContextHandle, **_: object) -> None:
    """有奖励确认浮窗就点确认，没有就什么都不做。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
    """
    if not home_checker.check_home_reward_confirm(ctx):
        return
    HomePage(ctx).click_reward_confirm()


# ── 导航边 ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class NavTarget:
    """从某个页面可以直达的一个目标。

    Attributes:
        target: 目标页面。
        action: 执行一次点击的动作，可接收调用方透传的参数。
        description: 这条边的说明，供维护与日志使用。
        confirm: 到达后是否需要确认；浮窗链的中间步判不了"到没到"，置假跳过。
    """

    target: PageName
    action: Callable[..., None]
    description: str = ''
    confirm: bool = True


# ── 页面 → 到达确认 ─────────────────────────────────────────────────────────

# 值统一收 (ctx, *, absent=False, attempts, interval_seconds)：前识别判出现，后识别
# （absent=True）判消失。识别节奏是各页面自己的默认值，定义在对应 checker 的签名里；
# 调用方需要覆盖时直接传参，注册表不再兼职配节奏。
_PAGE_CHECKERS: dict[PageName, Callable[..., bool]] = {
    PageName.LOGIN_PAGE: login_checker.check_login_page,
    PageName.SERVER_SELECT: login_checker.check_server_select,
    PageName.HOME: home_checker.check_home_page,
    PageName.HOME_NEWS: home_checker.check_home_news_page,
    PageName.HOME_REWARD: home_checker.check_home_reward_page,
    PageName.HOME_REWARD_CONFIRM: home_checker.check_home_reward_confirm_page,
    PageName.SORTIE_MAP: sortie_checker.check_sortie_page,
    PageName.EVENT_MAP: stage_push.check_event_map_page,
    PageName.EVENT_STAGE_OVERLAY: stage_push.check_event_sortie_prepare,
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
            PageName.HOME_NEWS,
            lambda ctx, **_: LoginPage(ctx).click_enter_game(
                login_checker.read_enter_button_center(ctx)
            ),
            '登录页 → 主页（经每日浮窗链）',
            confirm=False,
        ),
    ),
    PageName.SERVER_SELECT: (
        NavTarget(
            PageName.LOGIN_PAGE,
            lambda ctx, **params: LoginPage(ctx).click_server(
                _server_index(ctx, str(params['server']))
            ),
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
            PageName.HOME_NEWS,
            lambda ctx, **_: SortiePage(ctx).go_back(),
            '出征页 → 主页（经每日浮窗链）',
            confirm=False,
        ),
    ),
    # 每日浮窗链：进链的边只负责「走到这一步」，浮窗在不在由各自的动作自查；
    # 每一步的到达确认都关掉，因为「到了吗」取决于下一个浮窗是否存在，静态判不了。
    # 只有链尾「→ 主页」做真确认——那里才知道主页是否真的干净。
    PageName.HOME_NEWS: (
        NavTarget(
            PageName.HOME_REWARD,
            _close_daily_news,
            '每日公告 → 每日奖励',
            confirm=False,
        ),
    ),
    PageName.HOME_REWARD: (
        NavTarget(
            PageName.HOME_REWARD_CONFIRM,
            _claim_daily_reward,
            '每日奖励 → 每日奖励确认',
            confirm=False,
        ),
    ),
    PageName.HOME_REWARD_CONFIRM: (
        NavTarget(
            PageName.HOME,
            _confirm_daily_reward,
            '每日奖励确认 → 主页',
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
            PageName.HOME_NEWS,
            lambda ctx, **_: EventPage(ctx, event_type=_event_type(ctx)).go_back(),
            '活动地图 → 主页（经每日浮窗链）',
            confirm=False,
        ),
    ),
}


# ── 上下文辅助 ──────────────────────────────────────────────────────────────


def _server_index(ctx: ContextHandle, name: str) -> int:
    """把区服名换成它在列表中的固定位置。

    位置由 OCR 逐条比对得出；读不到时退回静态映射，保证换区链路不会因为一次识别失败而中断。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        name: 目标区服名，取值见 `login_checker.constants.SERVER_NAMES`。

    Returns:
        区服在列表中的位置序号（0 起）。
    """
    index = login_checker.find_server_position(ctx, name)
    if index is None:
        index = login_checker.server_index(name)
        _log.warning('[UI] 导航 → 区服定位兜底：server={!r}，position={}', name, index)
    return index


def _event_type(ctx: ContextHandle) -> str:
    """读取任务绑定的活动玩法标识。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        活动玩法标识。

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
    """返回某个页面可以直达的目标。

    Args:
        page: 起点页面。

    Returns:
        该页面的直达边；没有出边时为空元组。
    """
    return _NAV_TARGETS.get(page, ())


def get_checker(page: PageName) -> Callable[[ContextHandle], bool] | None:
    """返回某个页面的到达确认入口。

    Args:
        page: 目标页面。

    Returns:
        该页面的确认入口；未注册时为 None。
    """
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
