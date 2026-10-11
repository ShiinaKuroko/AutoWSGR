"""模块功能：提供导航器的统一入口。

上层调用：
- dispatch 与 business：把游戏带到登录页、请求到达某个页面或回退上一页。

下层依赖：
- navigation.registry：查询可达目标、到达确认与路径。
- navigation.types：页面契约与导航错误。
- dispatch.session：进程级会话状态。
- page_checker 与 controller.home.main_page：登录流程识别、主页识别与每日弹窗点击。

边界：编排启动流程、识别与算路；路径的执行与前后识别交给 navigation.executor；
不做页面坐标、业务流程与恢复决策，失败直接抛给调用方。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation import registry
from autowsgr.application.ui.navigation.executor import NavigationExecutor
from autowsgr.application.ui.navigation.page_checker import login_checker
from autowsgr.application.ui.navigation.types import (
    ManualUpdateRequiredError,
    NavigationError,
    PageName,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.dispatch.session import SessionState, get_session


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui.navigation')


# ── 流程参数 ────────────────────────────────────────────────────────────────

# 启动三信号里「黑屏」「加载中」是宽泛校验，识别不到就等这么久再看下一项。
_STARTUP_STEP_WAIT_SECONDS = 3.0
# 确认画面消失、读取更新提示与加载状态时的探测次数。
_PROBE_ATTEMPTS = 3
# 等登录页出现的最大识别次数，以及相邻两次识别的间隔秒数。
_LOGIN_PAGE_ATTEMPTS = 60
_STARTUP_INTERVAL_SECONDS = 1.0


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
        self._executor = NavigationExecutor(ctx, self._session)

    # ── 公开入口 ────────────────────────────────────────────────────────────

    def navigate_to(self, target: PageName, **params: object) -> None:
        """导航到目标页面。

        Args:
            target: 目标页面。
            **params: 透传给页面动作的参数（例如活动章节的 `node`）。

        Raises:
            NavigationError: 无法识别当前页面、没有可达路径或到达确认失败。
        """
        source = self._current_page()
        if source == target:
            _log.info('[UI] 导航 → 已在目标页面：target={!r}', target.value)
            return

        path = registry.find_path(source, target)
        _log.info('[UI] 导航 → 开始：source={!r}，target={!r}', source.value, target.value)
        self._executor.walk_forward(path, params)
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
        self._executor.walk_backward(registry.find_path(current, target))

    # ── 启动流程 ────────────────────────────────────────────────────────────

    def navigate_to_login(self) -> None:
        """把处于启动阶段的游戏带到「登录页」。

        启动三信号由游戏特性决定：
        - 「健康游戏提示」与「加载中」都是宽泛校验，识别不到就等一会儿再看下一项；
        - 「更新提示」是唯一的硬分支，它一旦弹出游戏必然卡死，识别到就抛错交人工处理。

        调用方负责在游戏没运行时拉起 App；本方法不碰进程，也不做换区。

        Raises:
            ManualUpdateRequiredError: 检测到游戏更新，需要人工处理。
            NavigationError: 启动超时，未出现登录页。
        """
        # 1. 健康游戏提示：能不能识别到不重要，识别不到就等一会儿。
        if login_checker.check_black_screen(self._ctx):
            login_checker.check_black_screen(
                self._ctx,
                absent=True,
                attempts=_PROBE_ATTEMPTS,
                interval_seconds=_STARTUP_INTERVAL_SECONDS,
            )
        else:
            time.sleep(_STARTUP_STEP_WAIT_SECONDS)

        # 2. 更新提示：唯一硬分支，弹出来游戏就卡在这里，只能人工处理。
        if login_checker.check_update_prompt(self._ctx):
            raise ManualUpdateRequiredError('检测到游戏更新，需要人工处理')

        # 3. 加载中：同样是宽泛校验，没在加载就往下走。
        if login_checker.check_loading(self._ctx):
            time.sleep(_STARTUP_STEP_WAIT_SECONDS)

        # 4. 等登录页出现；已经在登录页时这里会立刻通过。
        if not login_checker.check_login_page(
            self._ctx,
            attempts=_LOGIN_PAGE_ATTEMPTS,
            interval_seconds=_STARTUP_INTERVAL_SECONDS,
        ):
            raise NavigationError('启动超时：未出现登录页')

    # ── 内部实现 ────────────────────────────────────────────────────────────

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
