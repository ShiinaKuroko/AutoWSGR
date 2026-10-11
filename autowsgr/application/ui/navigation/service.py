"""模块功能：提供导航器的统一入口。

上层调用：
- dispatch 与 business：把游戏带到登录页、请求到达某个页面或回退上一页。

下层依赖：
- navigation.registry：查询可达目标、到达确认与路径。
- navigation.types：页面契约与导航错误。
- dispatch.session：进程级会话状态。
- page_checker 与 controller.home.main_page：登录流程识别、主页识别与每日弹窗点击。

边界：编排启动流程、识别、算路、执行与逐步确认；不做页面坐标、业务流程与恢复决策，
失败直接抛给调用方。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.runtime.types import LoginServer
from autowsgr.application.ui.controller.home.main_page import HomePage
from autowsgr.application.ui.navigation import registry
from autowsgr.application.ui.navigation.page_checker import home_checker, login_checker
from autowsgr.application.ui.navigation.types import (
    ManualUpdateRequiredError,
    NavigationError,
    NavTarget,
    PageName,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.dispatch.session import SessionState, get_session


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui.navigation')


# ── 启动流程参数 ────────────────────────────────────────────────────────────

# 拉起 App 后等待进程进入启动画面的时间，单位为秒。
_STARTUP_SETTLE_SECONDS = 5.0
# 等健康游戏提示出现的最大识别次数，以及相邻两次识别的间隔秒数。
_STARTUP_ATTEMPTS = 120
_STARTUP_INTERVAL_SECONDS = 1.0
# 确认画面消失、读取更新提示与加载状态时的探测次数。
_PROBE_ATTEMPTS = 3
# 等登录页出现的最大识别次数。
_LOGIN_PAGE_ATTEMPTS = 60
# 仍在加载时按用户定的兜底再探一次的等待时间，单位为秒。
_LOADING_RECHECK_WAIT_SECONDS = 3.0
# 强杀游戏后等待进程退出的时间，单位为秒。
_RESTART_SETTLE_SECONDS = 2.0


class NavigationService:
    """导航器入口。"""

    def __init__(self, ctx: ContextHandle, *, session: SessionState | None = None) -> None:
        """绑定任务上下文与进程级会话状态。

        Args:
            ctx: 提供设备服务与任务事实的 dispatch 上下文句柄。
            session: 进程级会话状态；缺省使用进程内单例。
        """
        self._ctx = ctx
        self._session = session or get_session()

    # ── 公开入口 ────────────────────────────────────────────────────────────

    def navigate_to(self, target: PageName, **params: object) -> None:
        """导航到目标页面。

        Args:
            target: 目标页面。
            **params: 透传给页面动作的参数（例如活动章节的 `node`）。

        Raises:
            NavigationError: 无法识别当前页面、没有可达路径或到达确认失败。
        """
        session = self._session
        source = self._current_page()
        if source == target:
            _log.info('[UI] 导航 → 已在目标页面：target={!r}', target.value)
            return

        path = registry.find_path(source, target)
        if self._passes_home(source, path):
            self._handle_daily_popup(session)
            source = self._current_page()
            if source == target:
                return
            path = registry.find_path(source, target)

        _log.info('[UI] 导航 → 开始：source={!r}，target={!r}', source.value, target.value)
        self._walk(path, params)
        _log.info('[UI] 导航 → 完成：target={!r}', target.value)

    def navigate_back(self) -> None:
        """回退到上一个页面。

        Raises:
            NavigationError: 导航栈为空或回退确认失败。
        """
        session = self._session
        current = self._current_page()
        session.pop_page()
        previous = session.current_page()
        if previous is None:
            session.push_page(current.value)
            raise NavigationError('导航栈为空，无法回退')

        target = PageName(previous)
        _log.info('[UI] 导航 → 回退：source={!r}，target={!r}', current.value, target.value)
        self._walk(registry.find_path(current, target), {})

    # ── 启动流程 ────────────────────────────────────────────────────────────

    def ensure_started(self) -> None:
        """把游戏带到「登录页」。

        启动段（健康游戏提示、更新提示、加载中）没有可导航的边，只能在这里编排；
        换区复用导航图的两条边。

        Raises:
            ManualUpdateRequiredError: 检测到游戏更新，需要人工处理。
            NavigationError: 启动超时、加载未完成或状态不明。
        """
        ctrl = self._ctx.runtime.ctrl
        package = self._ctx.runtime.config.account.package_name

        # 1. 游戏没运行就先拉起，等待进程进入启动画面。
        if not ctrl.is_app_running(package):
            _log.info('[UI] 启动 → 拉起游戏：package={!r}', package)
            ctrl.start_app(package)
            time.sleep(_STARTUP_SETTLE_SECONDS)

        # 2. 等健康游戏提示出现，再确认它已经切走。
        if not login_checker.check_black_screen(
            self._ctx,
            attempts=_STARTUP_ATTEMPTS,
            interval_seconds=_STARTUP_INTERVAL_SECONDS,
        ):
            raise NavigationError('启动超时：未出现健康游戏提示')
        login_checker.check_black_screen(
            self._ctx,
            absent=True,
            attempts=_PROBE_ATTEMPTS,
            interval_seconds=_STARTUP_INTERVAL_SECONDS,
        )

        # 3. 更新分支：后识别通过说明没有更新，前识别通过说明需要人工更新。
        if not login_checker.check_update_prompt(
            self._ctx,
            absent=True,
            attempts=_PROBE_ATTEMPTS,
            interval_seconds=_STARTUP_INTERVAL_SECONDS,
        ):
            if login_checker.check_update_prompt(self._ctx):
                raise ManualUpdateRequiredError('检测到游戏更新，需要人工处理')
            raise NavigationError('启动状态不明：无法确认是否需要更新')

        # 4. 加载分支：仍在加载时按用户定的兜底再探一次。
        if not login_checker.check_loading(
            self._ctx,
            absent=True,
            attempts=_PROBE_ATTEMPTS,
            interval_seconds=_STARTUP_INTERVAL_SECONDS,
        ):
            time.sleep(_LOADING_RECHECK_WAIT_SECONDS)
            if not login_checker.check_loading(
                self._ctx,
                absent=True,
                attempts=_PROBE_ATTEMPTS,
                interval_seconds=_STARTUP_INTERVAL_SECONDS,
            ):
                raise NavigationError('启动超时：游戏仍在加载')

        # 5. 等登录页出现。
        if not login_checker.check_login_page(
            self._ctx,
            attempts=_LOGIN_PAGE_ATTEMPTS,
            interval_seconds=_STARTUP_INTERVAL_SECONDS,
        ):
            raise NavigationError('启动超时：未出现登录页')

        # 6. 按用户设置完成一次换区。
        self._select_server()

    def restart_game(self) -> None:
        """SL：强杀游戏后重新走一遍启动流程。"""
        ctrl = self._ctx.runtime.ctrl
        package = self._ctx.runtime.config.account.package_name
        _log.warning('[UI] 启动 → 强制重启游戏：package={!r}', package)
        ctrl.stop_app(package)
        time.sleep(_RESTART_SETTLE_SECONDS)
        self.ensure_started()

    # ── 内部实现 ────────────────────────────────────────────────────────────

    def _select_server(self) -> None:
        """按用户设置完成一次区服选择；本次运行已选过则跳过。

        Raises:
            NavigationError: 换区路径无法确认到达。
        """
        session = self._session
        if session.server_selected:
            return

        wanted = self._ctx.runtime.config.account.game_server
        if wanted is LoginServer.default:
            session.mark_server_selected()
            return

        index = login_checker.find_server_position(self._ctx, wanted.value)
        if index is None:
            # 区服列表位置固定，OCR 读不到时按静态映射兜底。
            index = login_checker.server_index(wanted.value)
            _log.warning('[UI] 启动 → 区服定位兜底：server={!r}，position={}', wanted.value, index)

        self.navigate_to(PageName.SERVER_SELECT)
        self.navigate_to(PageName.LOGIN_PAGE, position=index)
        session.mark_server_selected()

    def _walk(self, path: tuple[NavTarget, ...], params: dict[str, object]) -> None:
        """按路径逐步执行动作并确认到达。

        Raises:
            NavigationError: 某一步的到达确认失败。
        """
        session = self._session
        for edge in path:
            edge.action(self._ctx, **params)
            confirm = registry.get_checker(edge.target)
            if confirm is not None and not confirm(self._ctx):
                raise NavigationError(f'到达确认失败：{edge.description!r}')
            session.push_page(edge.target.value)

    def _current_page(self) -> PageName:
        """返回当前页面：优先取导航栈顶，栈空时识别一次。"""
        session = self._session
        current = session.current_page()
        if current is not None:
            return PageName(current)
        page = self._detect_page()
        session.push_page(page.value)
        return page

    def _detect_page(self) -> PageName:
        """遍历所有确认入口，判断当前在哪一页。

        Raises:
            NavigationError: 所有确认入口都识别不到。
        """
        for page in PageName:
            confirm = registry.get_checker(page)
            if confirm is not None and confirm(self._ctx):
                _log.info('[UI] 导航 → 识别当前页面：page={!r}', page.value)
                return page
        raise NavigationError('无法识别当前页面')

    @staticmethod
    def _passes_home(source: PageName, path: tuple[NavTarget, ...]) -> bool:
        """判断本次导航是否经过首页。"""
        if source is PageName.HOME:
            return True
        return any(edge.target is PageName.HOME for edge in path)

    def _handle_daily_popup(self, session: SessionState) -> None:
        """经过首页时处理每日弹窗：公告与奖励各自独立检测。"""
        if session.daily_popup_handled:
            return
        self._handle_daily_news()
        self._handle_daily_reward()
        session.mark_daily_popup_handled()

    def _handle_daily_news(self) -> None:
        """处理每日公告：存在则勾选（未勾选才点）、关闭、确认消失。

        Raises:
            NavigationError: 关闭后公告仍然存在。
        """
        state = home_checker.check_home_news_overlay(self._ctx)
        if not state.matched:
            return

        page = HomePage(self._ctx)
        _log.info('[UI] 导航 → 每日公告：checked={!r}', state.checked)
        if state.checked is False:
            page.click_news_checkbox()
        page.click_news_close()
        if home_checker.check_home_news_overlay(self._ctx).matched:
            raise NavigationError('每日公告关闭后仍然存在')

    def _handle_daily_reward(self) -> None:
        """处理每日奖励：存在则领取、确认、确认消失。

        Raises:
            NavigationError: 领取后没有确认浮窗，或确认后浮窗仍然存在。
        """
        if not home_checker.check_home_reward_overlay(self._ctx):
            return

        page = HomePage(self._ctx)
        _log.info('[UI] 导航 → 每日奖励：开始')
        page.click_reward_claim()
        if not home_checker.check_home_reward_confirm(self._ctx):
            raise NavigationError('领取每日奖励后未出现确认浮窗')
        page.click_reward_confirm()
        if home_checker.check_home_reward_confirm(self._ctx):
            raise NavigationError('确认后奖励浮窗仍然存在')
