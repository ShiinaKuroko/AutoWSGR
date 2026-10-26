"""模块功能：维护页面之间的可达列表与到达确认。

上层调用：
- application.ui.navigation.service：查询可达目标、到达确认与完整路径。

下层依赖：
- navigation.types：提供页面契约与错误。
- navigation.checker：提供到达确认入口。
- application.ui.controller：提供一次点击的动作。

边界：只维护"能去哪、怎么去、到了吗"，不截图、不点击、不判断业务状态。
每条边就是一行数据，不为边写转发函数。
"""

from __future__ import annotations

import functools
from collections import deque
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.backyard.main_page import (
    BackyardPage,
    BackyardTarget,
)
from autowsgr.application.ui.controller.home.event_page import EventPage
from autowsgr.application.ui.controller.home.main_page import HomePage, Target
from autowsgr.application.ui.controller.login import LoginPage
from autowsgr.application.ui.controller.operations.mission_page import MissionPage
from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    SortiePage,
    SortieTab,
)
from autowsgr.application.ui.controller.sidebar.build_page import BuildPage, BuildTab
from autowsgr.application.ui.controller.sidebar.friend_page import FriendPage
from autowsgr.application.ui.controller.sidebar.intensify_page import (
    IntensifyPage,
    IntensifyTab,
)
from autowsgr.application.ui.controller.sidebar.main_page import SidebarPage, SidebarTarget
from autowsgr.application.ui.navigation.checker import (
    backyard,
    home,
    login,
    mission,
    sidebar,
    sortie,
)
from autowsgr.application.ui.navigation.checker.event import stage_push
from autowsgr.application.ui.navigation.checker.sidebar import build, intensify
from autowsgr.application.ui.navigation.checker.sidebar.friend import check_friend_page
from autowsgr.application.ui.navigation.types import (
    NavigationError,
    NavTab,
    NavTarget,
    PageName,
)
from autowsgr.dispatch.session import DailyPopup, get_session


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.dispatch.context import ContextHandle


# ── 每日浮窗动作 ────────────────────────────────────────────────────────────

# 浮窗链的每一步都"先问再做"：不在就什么都不做，避免空点；到达确认由边自己关掉。


def _close_daily_news(ctx: ContextHandle, **_: object) -> None:
    """有每日公告就关掉，没有就什么都不做。

    未勾选「今日不再显示」时先勾上，避免第二天又弹。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
    """
    state = home.read_news_overlay(ctx)
    if not state.matched:
        return
    page = HomePage(ctx)
    if state.checked is False:
        page.click_news_checkbox()
        # 勾选有反馈：等它真的勾上再关闭，没勾上就不关，留给下次。
        if not home.check_news_checked(ctx):
            return
    page.click_news_close()
    # 关闭有动画：确认它真的让开了再记标记——记下就意味着后续不再识别这个浮窗。
    if home.read_news_overlay(ctx).matched:
        return
    get_session().mark_popup_settled(DailyPopup.NEWS)


def _settle_to_sidebar(ctx: ContextHandle, **_: object) -> None:
    """清完浮窗后落到侧边栏：已经在侧边栏就不动，还在主页就点入口进去。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
    """
    if sidebar.check_sidebar_page(
        ctx,
        attempts=_SIDEBAR_SETTLE_ATTEMPTS,
        interval_seconds=_SIDEBAR_SETTLE_INTERVAL_SECONDS,
    ):
        return
    HomePage(ctx).go_to(Target.SIDEBAR)


# 侧边栏展开与收起都有动画（约 1.5 秒）。判断「在不在」和等它「让没让开」都要给足窗口：
# 5 次 x 0.4 秒，约 2 秒，留出余量。命中即返回，侧边栏真在时不会白等。
_SIDEBAR_SETTLE_ATTEMPTS = 5
_SIDEBAR_SETTLE_INTERVAL_SECONDS = 0.4


def _settle_to_home(ctx: ContextHandle, **_: object) -> None:
    """清完浮窗后回主页：奖励确认浮窗还在就点掉，停在侧边栏就关掉它。

    浮窗盖在主页上时（从任务、出征、后来）这一段什么都不用做，直接确认主页即可。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
    """
    _confirm_daily_reward(ctx)
    if sidebar.check_sidebar_page(
        ctx,
        attempts=_SIDEBAR_SETTLE_ATTEMPTS,
        interval_seconds=_SIDEBAR_SETTLE_INTERVAL_SECONDS,
    ):
        SidebarPage(ctx).go_back()
        # 收起同样有动画，等它真的让开再交给到达确认。
        sidebar.check_sidebar_page(
            ctx,
            absent=True,
            attempts=_SIDEBAR_SETTLE_ATTEMPTS,
            interval_seconds=_SIDEBAR_SETTLE_INTERVAL_SECONDS,
        )


# 领取后确认浮窗出现要走动画和网络，窗口比普通浮窗长一些。
_CLAIM_CONFIRM_ATTEMPTS = 8


def _claim_daily_reward(ctx: ContextHandle, **_: object) -> None:
    """有每日奖励就领取，没有就什么都不做。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
    """
    if not home.check_home_reward_overlay(ctx):
        return
    HomePage(ctx).click_reward_claim()
    # 领取后确认浮窗会盖上来，领取按钮仍在画面里；等确认浮窗出现才算领取完成。
    if not home.check_home_reward_confirm(ctx, attempts=_CLAIM_CONFIRM_ATTEMPTS):
        return
    get_session().mark_popup_settled(DailyPopup.REWARD)


def _confirm_daily_reward(ctx: ContextHandle, **_: object) -> None:
    """有奖励确认浮窗就点确认，没有就什么都不做。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
    """
    if not home.check_home_reward_confirm(ctx):
        return
    HomePage(ctx).click_reward_confirm()
    # 确认后有动画：确认浮窗真的让开了再记标记。
    if home.check_home_reward_confirm(ctx):
        return
    get_session().mark_popup_settled(DailyPopup.REWARD_CONFIRM)


def _claim_all_mission_rewards(ctx: ContextHandle, **_: object) -> None:
    """任务页有「全部领取」就点，没有就什么都不做。

    按钮只在有奖励可领时出现，不遮挡任务页，因此不是页面；
    这一步和浮窗链的每一步一样「先问再做」，避免空点。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
    """
    if not mission.check_claim_all_button(ctx):
        return
    MissionPage(ctx).click_claim_all()


# ── 页面 → 到达确认 ─────────────────────────────────────────────────────────

# 值统一收 (ctx, *, absent=False, attempts, interval_seconds)：前识别判出现，后识别
# （absent=True）判消失。识别节奏是各页面自己的默认值，定义在对应 checker 的签名里；
# 调用方需要覆盖时直接传参，注册表不再兼职配节奏。
# ── 域探针 ─────────────────────────────────────────────────────────────────

# 一个域一次读一帧，直接返回本域当前命中的层。home 的四个页面共享同一组模板，
# 逐页调用会把同一帧读四遍，因此按域聚合。
_DOMAIN_PROBERS: tuple[Callable[[ContextHandle], PageName | None], ...] = (home.read_home_layer,)

# 由域探针负责的页面；它们不再登记到逐页注册表。
_DOMAIN_PAGES: frozenset[PageName] = frozenset(
    {
        PageName.HOME,
        PageName.HOME_NEWS,
        PageName.HOME_REWARD,
        PageName.HOME_REWARD_CONFIRM,
    }
)


_PAGE_CHECKERS: dict[PageName, Callable[..., bool]] = {
    PageName.LOGIN_PAGE: login.check_login_page,
    PageName.SERVER_SELECT: login.check_server_select,
    PageName.SORTIE_MAP: sortie.check_sortie_page,
    PageName.EVENT_MAP: stage_push.check_event_map_page,
    PageName.EVENT_STAGE_OVERLAY: stage_push.check_event_sortie_prepare,
    PageName.SIDEBAR: sidebar.check_sidebar_page,
    PageName.BUILD_SUBMENU: sidebar.check_build_submenu,
    PageName.INTENSIFY_SUBMENU: sidebar.check_intensify_submenu,
    PageName.BUILD: build.check_build_page,
    PageName.INTENSIFY: intensify.check_intensify_page,
    PageName.FRIEND: check_friend_page,
    PageName.MISSION: mission.check_mission_page,
    PageName.MISSION_REWARD_CONFIRM: mission.check_mission_reward_confirm,
    PageName.BACKYARD: backyard.check_backyard_page,
    PageName.CANTEEN: backyard.check_canteen_page,
    PageName.ACADEMY: backyard.check_academy_page,
    PageName.RANK_ROOM: backyard.check_rank_room_page,
    PageName.BATH: backyard.check_bath_page,
}

# ── 页面 → 标签表 ───────────────────────────────────────────────────────────

# 只登记"非默认标签"：默认标签就是页面本身，页面级 checker 已经认它。
# 键是 navigate_to 的 tab 入参，与各页面控制器里标签枚举的 name 小写形式一致。
_TABS: dict[PageName, dict[str, NavTab]] = {
    PageName.SORTIE_MAP: {
        # 出征是默认标签，但远征可收时进入会停在远征，注册一个用于切回来。
        'sortie': NavTab(
            lambda ctx: SortiePage(ctx).go_to(SortieTab.SORTIE),
            sortie.check_sortie_page,
            '出征',
        ),
        'exercise': NavTab(
            lambda ctx: SortiePage(ctx).go_to(SortieTab.EXERCISE),
            sortie.check_exercise_page,
            '演习',
        ),
        'expedition': NavTab(
            lambda ctx: SortiePage(ctx).go_to(SortieTab.EXPEDITION),
            sortie.check_expedition_page,
            '远征',
        ),
        'campaign': NavTab(
            lambda ctx: SortiePage(ctx).go_to(SortieTab.CAMPAIGN),
            sortie.check_campaign_page,
            '战役',
        ),
        'decisive': NavTab(
            lambda ctx: SortiePage(ctx).go_to(SortieTab.DECISIVE),
            sortie.check_decisive_page,
            '决战',
        ),
    },
    PageName.BUILD: {
        'destroy': NavTab(
            lambda ctx: BuildPage(ctx).go_to_tab(BuildTab.DESTROY),
            build.check_dismantle_tab,
            '解体',
        ),
    },
    PageName.INTENSIFY: {
        'remold': NavTab(
            lambda ctx: IntensifyPage(ctx).go_to_tab(IntensifyTab.REMOLD),
            intensify.check_remold_tab,
            '改造',
        ),
        'skill': NavTab(
            lambda ctx: IntensifyPage(ctx).go_to_tab(IntensifyTab.SKILL),
            intensify.check_skill_tab,
            '技能',
        ),
    },
}


# ── 活动地图动作 ────────────────────────────────────────────────────────────


def _event_map_to_overlay(ctx: ContextHandle, **params: object) -> None:
    """把地图切到目标章节的难度，再点开该章节的浮窗。

    普通与困难共用同一批落点，难度不对就会点开"同名但错误的"章节；因此进浮窗之前
    先对齐难度。难度是否切到位由 checker 按导航确认节奏判定，这里不自己配节奏。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        **params: 可选的 `stage`（章节标识，例如 EX7）；缺省取任务绑定的 event_stage。

    Raises:
        NavigationError: 读不到模式按钮中心，或难度没有切到目标值。
    """
    event_type = stage_push.read_event_type(ctx)
    parsed = stage_push.parse_stage(
        str(params['stage']) if 'stage' in params else stage_push.read_event_stage(ctx)
    )

    state = stage_push.read_event_map_state(ctx, event_type=event_type)
    if state.current_mode is not parsed.difficulty:
        center = stage_push.read_mode_button_center(ctx, event_type=event_type)
        if center is None:
            raise NavigationError('切换活动难度失败：读不到模式按钮中心')
        EventPage(ctx, event_type=event_type).switch_difficulty(center)
        if not stage_push.wait_event_mode(ctx, event_type=event_type, mode=parsed.difficulty):
            raise NavigationError(f'切换活动难度失败：未切到 {parsed.difficulty.value!r}')

    EventPage(ctx, event_type=event_type).go_to_overlay(parsed.node)


# ── 页面 → 可达列表 ─────────────────────────────────────────────────────────

_NAV_TARGETS: dict[PageName, tuple[NavTarget, ...]] = {
    PageName.LOGIN_PAGE: (
        NavTarget(
            PageName.SERVER_SELECT,
            lambda ctx, **_: LoginPage(ctx).click_switch_entry(login.read_switch_entry_center(ctx)),
            '登录页 → 区服选择页',
        ),
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: LoginPage(ctx).click_enter_game(login.read_enter_button_center(ctx)),
            '登录页 → 主页（经每日浮窗链）',
            confirm=False,
        ),
    ),
    PageName.SERVER_SELECT: (
        NavTarget(
            PageName.LOGIN_PAGE,
            lambda ctx, **params: LoginPage(ctx).click_server(
                login.read_server_index(ctx, str(params['server']))
            ),
            '区服选择页 → 登录页',
        ),
    ),
    PageName.HOME: (
        NavTarget(
            PageName.SORTIE_MAP,
            lambda ctx, **_: HomePage(ctx).go_to(Target.SORTIE),
            '首页 → 出征页',
            tab='sortie',
        ),
        NavTarget(
            PageName.EVENT_MAP,
            lambda ctx, **_: HomePage(ctx).go_to(Target.EVENT),
            '首页 → 活动地图',
        ),
        NavTarget(
            PageName.SIDEBAR,
            lambda ctx, **_: HomePage(ctx).go_to(Target.SIDEBAR),
            '首页 → 侧边栏',
        ),
        NavTarget(
            PageName.MISSION,
            lambda ctx, **_: HomePage(ctx).go_to(Target.TASK),
            '首页 → 任务页',
        ),
        NavTarget(
            PageName.BACKYARD,
            lambda ctx, **_: HomePage(ctx).go_to(Target.BACKYARD),
            '首页 → 后院主页',
        ),
    ),
    # 后院：主页进四个二级页；二级页可以退回后院主页（跨二级页跳转靠它中转），
    # 也可以点通用回首页按钮直接回主页。回主页的边照常走每日浮窗链。
    PageName.BACKYARD: (
        NavTarget(
            PageName.CANTEEN,
            lambda ctx, **_: BackyardPage(ctx).go_to(
                BackyardTarget.CANTEEN,
                backyard.read_canteen_entry_center(ctx),
            ),
            '后院主页 → 餐厅',
        ),
        NavTarget(
            PageName.ACADEMY,
            lambda ctx, **_: BackyardPage(ctx).go_to(
                BackyardTarget.ACADEMY,
                backyard.read_academy_entry_center(ctx),
            ),
            '后院主页 → 学院',
        ),
        NavTarget(
            PageName.RANK_ROOM,
            lambda ctx, **_: BackyardPage(ctx).go_to(
                BackyardTarget.RANK_ROOM,
                backyard.read_rank_room_entry_center(ctx),
            ),
            '后院主页 → 军阶室',
        ),
        NavTarget(
            PageName.BATH,
            lambda ctx, **_: BackyardPage(ctx).go_to(
                BackyardTarget.BATH,
                backyard.read_bath_entry_center(ctx),
            ),
            '后院主页 → 浴室',
        ),
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: BackyardPage(ctx).go_back(),
            '后院主页 → 主页（经每日浮窗链）',
            confirm=False,
        ),
    ),
    PageName.CANTEEN: (
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: BackyardPage(ctx).go_home(),
            '餐厅 → 主页（经每日浮窗链）',
            confirm=False,
        ),
        NavTarget(
            PageName.BACKYARD,
            lambda ctx, **_: BackyardPage(ctx).go_back(),
            '餐厅 → 后院主页',
        ),
    ),
    PageName.ACADEMY: (
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: BackyardPage(ctx).go_home(),
            '学院 → 主页（经每日浮窗链）',
            confirm=False,
        ),
        NavTarget(
            PageName.BACKYARD,
            lambda ctx, **_: BackyardPage(ctx).go_back(),
            '学院 → 后院主页',
        ),
    ),
    PageName.RANK_ROOM: (
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: BackyardPage(ctx).go_home(),
            '军阶室 → 主页（经每日浮窗链）',
            confirm=False,
        ),
        NavTarget(
            PageName.BACKYARD,
            lambda ctx, **_: BackyardPage(ctx).go_back(),
            '军阶室 → 后院主页',
        ),
    ),
    PageName.BATH: (
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: BackyardPage(ctx).go_home(),
            '浴室 → 主页（经每日浮窗链）',
            confirm=False,
        ),
        NavTarget(
            PageName.BACKYARD,
            lambda ctx, **_: BackyardPage(ctx).go_back(),
            '浴室 → 后院主页',
        ),
    ),
    # 任务页：领奖按钮在就点，点完弹「获得」浮窗；回主页照常走每日浮窗链。
    PageName.MISSION: (
        NavTarget(
            PageName.MISSION_REWARD_CONFIRM,
            _claim_all_mission_rewards,
            '任务页 → 获得浮窗',
            confirm=False,
        ),
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: MissionPage(ctx).go_back(),
            '任务页 → 主页（经每日浮窗链）',
            confirm=False,
        ),
    ),
    PageName.MISSION_REWARD_CONFIRM: (
        NavTarget(
            PageName.MISSION,
            lambda ctx, **_: MissionPage(ctx).click_reward_confirm(),
            '获得浮窗 → 任务页',
        ),
    ),
    # 侧边栏体系：三个一级条目各进一个域，回主页一律点空白处直连，
    # 不走每日浮窗链——进侧边栏之前当天的浮窗早已处理过。
    PageName.SIDEBAR: (
        NavTarget(
            PageName.BUILD_SUBMENU,
            lambda ctx, **_: SidebarPage(ctx).go_to(SidebarTarget.BUILD),
            '侧边栏 → 建造二级菜单',
        ),
        NavTarget(
            PageName.INTENSIFY_SUBMENU,
            lambda ctx, **_: SidebarPage(ctx).go_to(SidebarTarget.INTENSIFY),
            '侧边栏 → 强化二级菜单',
        ),
        NavTarget(
            PageName.FRIEND,
            lambda ctx, **_: SidebarPage(ctx).go_to(SidebarTarget.FRIEND),
            '侧边栏 → 好友页面',
        ),
        NavTarget(
            PageName.HOME,
            lambda ctx, **_: SidebarPage(ctx).go_back(),
            '侧边栏 → 主页面（不经每日浮窗链）',
        ),
    ),
    PageName.BUILD_SUBMENU: (
        NavTarget(
            PageName.BUILD,
            lambda ctx, **_: SidebarPage(ctx).go_to_submenu(SidebarTarget.BUILD),
            '建造二级菜单 → 建造页',
        ),
        NavTarget(
            PageName.HOME,
            lambda ctx, **_: SidebarPage(ctx).go_back(),
            '建造二级菜单 → 主页面（不经每日浮窗链）',
        ),
    ),
    PageName.INTENSIFY_SUBMENU: (
        NavTarget(
            PageName.INTENSIFY,
            lambda ctx, **_: SidebarPage(ctx).go_to_submenu(SidebarTarget.INTENSIFY),
            '强化二级菜单 → 改造页',
        ),
        NavTarget(
            PageName.HOME,
            lambda ctx, **_: SidebarPage(ctx).go_back(),
            '强化二级菜单 → 主页面（不经每日浮窗链）',
        ),
    ),
    PageName.BUILD: (
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: BuildPage(ctx).go_back(),
            '建造页 → 主页面（经每日浮窗链）',
            confirm=False,
        ),
    ),
    PageName.INTENSIFY: (
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: IntensifyPage(ctx).go_back(),
            '改造页 → 主页面（经每日浮窗链）',
            confirm=False,
        ),
    ),
    PageName.FRIEND: (
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: FriendPage(ctx).go_back(),
            '好友页面 → 主页面（经每日浮窗链）',
            confirm=False,
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
    # 浮窗插在侧边栏（从好友、建造、改造来）或主页（从任务、出征、后来）上面，
    # 清完浮窗后落点因此有两种：已在侧边栏、或仍在主页。两条出边各自先判断，
    # 已经在目标层就什么都不点，避免点到别的东西。
    PageName.HOME_REWARD_CONFIRM: (
        NavTarget(
            PageName.SIDEBAR,
            _settle_to_sidebar,
            '每日奖励确认 → 侧边栏',
        ),
        NavTarget(
            PageName.HOME,
            _settle_to_home,
            '每日奖励确认 → 主页',
        ),
    ),
    PageName.EVENT_STAGE_OVERLAY: (
        NavTarget(
            PageName.EVENT_MAP,
            lambda ctx, **_: EventPage(
                ctx, event_type=stage_push.read_event_type(ctx)
            ).click_overlay_close(),
            '活动章节浮窗 → 活动地图',
        ),
    ),
    PageName.EVENT_MAP: (
        NavTarget(
            PageName.EVENT_STAGE_OVERLAY,
            _event_map_to_overlay,
            '活动地图 → 章节浮窗',
        ),
        NavTarget(
            PageName.HOME_NEWS,
            lambda ctx, **_: EventPage(ctx, event_type=stage_push.read_event_type(ctx)).go_back(),
            '活动地图 → 主页（经每日浮窗链）',
            confirm=False,
        ),
    ),
}


# ── 查询入口 ────────────────────────────────────────────────────────────────


def popups_all_settled() -> bool:
    """今天的三个每日浮窗是否都已处理。"""
    return home.popups_all_settled()


def on_arrival(ctx: ContextHandle, page: PageName) -> None:
    """到达某个页面后刷新会话记账。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        page: 刚确认到达的页面。
    """
    if page is PageName.HOME:
        home.mark_popups_settled(ctx)


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


def probe_domains(ctx: ContextHandle) -> tuple[PageName, ...]:
    """探测所有域，返回本帧命中的页面。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        域探针命中的页面；一个都没命中时为空元组。
    """
    hits: list[PageName] = []
    for prober in _DOMAIN_PROBERS:
        layer = prober(ctx)
        if layer is not None:
            hits.append(layer)
    return tuple(hits)


def is_domain_page(page: PageName) -> bool:
    """判断页面是否由域探针负责。

    Args:
        page: 待查询的页面。

    Returns:
        该页面由域探针负责时为真。
    """
    return page in _DOMAIN_PAGES


def get_tabs(page: PageName) -> dict[str, NavTab]:
    """返回某个页面登记过的非默认标签。

    Args:
        page: 页面名称。

    Returns:
        标签键到标签描述的映射；该页面没有标签时为空字典。
    """
    return _TABS.get(page, {})


# 不可达页面在深度排序里排最后：它们不该盖住任何可达页面。
_UNREACHABLE_DEPTH = 1 << 30


@functools.cache
def depth_of(page: PageName) -> int:
    """页面在导航图里的深度：从主页出发的最短跳数。

    图写在代码里、运行期不变，所以结果可以跨调用记忆；进程重启后重算，
    值完全一样，没有正确性影响。不可达的页面排在最深处。

    Args:
        page: 待查询的页面。

    Returns:
        最短跳数；主页为 0，不可达返回 `_UNREACHABLE_DEPTH`。
    """
    try:
        return len(find_path(PageName.HOME, page))
    except NavigationError:
        return _UNREACHABLE_DEPTH


def find_path(
    source: PageName,
    target: PageName,
    *,
    exclude: frozenset[PageName] = frozenset(),
) -> tuple[NavTarget, ...]:
    """在可达列表上广度拼接出从 source 到 target 的路径。

    Args:
        source: 起点页面。
        target: 目标页面。
        exclude: 本次算路不经过的页面；用于跳过已经处理过的每日浮窗，
            让路径改走它们的直连边。

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
            if edge.target in visited or edge.target in exclude:
                continue
            next_path = (*path, edge)
            if edge.target == target:
                return next_path
            visited.add(edge.target)
            queue.append((edge.target, next_path))
    raise NavigationError(f'没有从 {source.value!r} 到 {target.value!r} 的可达路径')


__all__ = [
    'depth_of',
    'find_path',
    'get_checker',
    'get_tabs',
    'get_targets',
    'is_domain_page',
    'on_arrival',
    'popups_all_settled',
    'probe_domains',
]
