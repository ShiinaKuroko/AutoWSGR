"""初始化步骤 — 执行器的永远第一步。

终态契约:
    无论从什么状态进入, 结束时游戏必定 [首页 + 浮层已清 + 待机]。
    幂等: 任何时候调用, 结果一致。SL / 异常恢复也复用本步骤回到已知状态。

三分支:
    1. 已在首页           → 清每日浮层 → 待机
    2. 游戏内其他页面      → goto_page 导航回首页 → 清浮层 → 待机
    3. 非游戏页面         → 启动游戏 → 登录 (新 login.yaml 坐标) → 首页 → 清浮层 → 待机

兜底 (SL):
    页面异常 (识别不出 / 导航超时) → 强制重启游戏, 只试 1 次 (防死循环),
    仍失败 → 抛 RuntimeError 给调度器。

依赖 (各归其位):
    - application.ui.navigation — 页面导航与识别
    - application.ui.controller.home.main_page.HomePage — 主页识别 (浮层命中 = 主页命中)
    - application.ui.controller.login.LoginPage — 启动画面识别与点击进入
    - 同包 overlays — 每日弹窗 (日期门控)
    - 同包 updater — 更新空判断 (未来扩展)
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.runtime.initialize import updater
from autowsgr.application.runtime.types import GameAPP
from autowsgr.application.ui.navigation import goto_page
from autowsgr.application.ui.navigation.page_checker.home_checker import check_home_page
from autowsgr.application.ui.navigation.service import NavigationError
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.common.system.logger import get_logger
from autowsgr.dispatch.context import context


if TYPE_CHECKING:
    from autowsgr.application.runtime import RuntimeContext as GameContext


_log = get_logger('business.initialize')

# ═══════════════════════════════════════════════════════════════════════════════
# 常量 (超时沿用旧值)
# ═══════════════════════════════════════════════════════════════════════════════

_STARTUP_TIMEOUT = 120.0
"""等待启动画面出现的超时 (秒)。"""

_STARTUP_POLL_INTERVAL = 1.0
"""启动等待轮询间隔 (秒)。"""

_ENTER_MAIN_TIMEOUT = 30.0
"""点击「进入游戏」后等待到达主页面超时 (秒)。"""

_RECOVERY_TIMEOUT = 20.0
"""页面异常恢复 (导航回首页) 的超时 (秒)。"""

_RECOVERY_RETRY_INTERVAL = 1.0
"""恢复重试间隔 (秒)。"""

_RESTART_SETTLE = 2.0
"""强杀游戏后等待进程退出的时间 (秒)。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════════════════


def initialize(ctx: GameContext) -> None:
    """初始化: 任意状态 → 首页 + 浮层已清 + 待机。

    Raises
    ------
    RuntimeError
        SL 强制重启后仍未到达主页面 (初始化失败, 交给调度器处置)。
    TimeoutError
        启动流程超时 (启动画面未出现 / 进入主页面超时)。
    """
    package = _package_of(ctx)
    _log.info('[Initialize] 初始化开始 (package={})', package)

    # 分支 3 前置: 游戏未运行 → 走启动流程
    if not ctx.ctrl.is_app_running(package):
        _log.info('[Initialize] 游戏未运行, 执行启动流程')
        _start_game_flow(ctx, package)

    # 分支 1/2: 已在首页, 或导航回首页
    if _try_reach_main(ctx):
        _log.info('[Initialize] 初始化完成, 首页待机')
        return

    # 兜底: SL 强制重启, 只试 1 次 (防死循环)
    _log.warning('[Initialize] 无法回到首页, 执行 SL 强制重启')
    _restart_game(ctx, package)
    if _try_reach_main(ctx):
        _log.info('[Initialize] SL 重启后初始化完成, 首页待机')
        return

    raise RuntimeError('初始化失败: SL 强制重启后仍未到达主页面')


# ═══════════════════════════════════════════════════════════════════════════════
# 辅助: 配置 / 状态查询
# ═══════════════════════════════════════════════════════════════════════════════


def _package_of(ctx: GameContext) -> str:
    """从配置取游戏包名 (account.game_app → Android 包名)。"""
    app = ctx.config.account.game_app
    if isinstance(app, GameAPP):
        return app.package_name
    return GameAPP(str(app)).package_name


def _is_on_home_page(ctx: GameContext) -> bool:
    """处理主页浮层后，用最新截图确认主页状态。"""
    matched = check_home_page(context.request())
    ctx.daily_overlay_checked = True
    return matched


# ═══════════════════════════════════════════════════════════════════════════════
# 分支 1/2: 到达主页面
# ═══════════════════════════════════════════════════════════════════════════════


def _try_reach_main(ctx: GameContext) -> bool:
    """调用统一导航入口到达主页，已在主页时由导航器直接短路确认。"""
    deadline = time.monotonic() + _RECOVERY_TIMEOUT
    while time.monotonic() < deadline:
        try:
            result = goto_page(ctx, PageName.HOME)
        except NavigationError:
            time.sleep(_RECOVERY_RETRY_INTERVAL)
        else:
            return result.confirmed

    _log.warning('[Initialize] 恢复主页面超时 ({:.0f}s)', _RECOVERY_TIMEOUT)
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# 分支 3: 启动流程
# ═══════════════════════════════════════════════════════════════════════════════


def _start_game_flow(ctx: GameContext, package: str) -> None:
    """冷启动流程: 拉起游戏 → 等启动画面 → 更新检测 → 点进入 → 验证首页。"""
    _log.info('[Initialize] 启动游戏 (package={})', package)
    ctx.ctrl.start_app(package)

    # ① 等待「点击进入」启动画面
    if not _wait_for_start_screen(ctx):
        raise TimeoutError(f'游戏启动超时 ({_STARTUP_TIMEOUT:.0f}s), 未出现启动画面')

    # ② 更新检测 (空判断, 未来扩展: 更新界面识别与处理)
    if updater.needs_update(ctx.ctrl.screenshot()):
        _log.info('[Initialize] 检测到游戏更新, 交由 updater 处理')
        updater.handle(ctx.ctrl)
        return

    # ③ 点击「进入游戏」(页面控制器内部读 login.yaml 坐标 + 等待稳定)
    _enter_game(ctx)

    # ④ 验证真的到达主页面 (旧代码缺这一步)
    if not _wait_for_home_page(ctx):
        raise TimeoutError(f'点击进入后超时 ({_ENTER_MAIN_TIMEOUT:.0f}s), 未到达主页面')


def _wait_for_start_screen(ctx: GameContext, *, timeout: float = _STARTUP_TIMEOUT) -> bool:
    """轮询等待「点击进入」启动画面出现。"""
    from autowsgr.application.ui.controller.login import LoginPage

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if LoginPage.check_current_page(ctx.ctrl.screenshot()):
            _log.info('[Initialize] 检测到启动画面')
            return True
        time.sleep(_STARTUP_POLL_INTERVAL)
    return False


def _enter_game(ctx: GameContext) -> None:
    """点击「进入游戏」按钮并复用登录启动画面控制器。"""
    from autowsgr.application.ui.controller.login import LoginPage

    LoginPage(ctx.ctrl).enter_game()


def _wait_for_home_page(ctx: GameContext, *, timeout: float = _ENTER_MAIN_TIMEOUT) -> bool:
    """登录后轮询主页完整检查，首次调用会先处理每日浮层。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _is_on_home_page(ctx):
            _log.info('[Initialize] 已到达主页面')
            return True
        time.sleep(_STARTUP_POLL_INTERVAL)
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# 兜底: SL 重启
# ═══════════════════════════════════════════════════════════════════════════════


def _restart_game(ctx: GameContext, package: str) -> None:
    """SL: 强杀游戏后冷启动 (解决战斗引擎的抽象泄露 — 重启归初始化管)。"""
    _log.warning('[Initialize] 强制重启游戏 (SL)')
    ctx.ctrl.stop_app(package)
    time.sleep(_RESTART_SETTLE)
    _start_game_flow(ctx, package)
