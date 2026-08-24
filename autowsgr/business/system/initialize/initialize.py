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
    - business/system/navigate.goto_page / identify_current_page — 页面导航与识别
    - infra/base/ui/pages/main_page.MainPage — 主页识别 (浮层命中 = 主页命中)
    - infra/base/ui/pages/start_screen.StartScreenPage — 启动画面识别与点击进入
    - 同包 overlays — 每日弹窗 (日期门控)
    - 同包 updater — 更新空判断 (未来扩展)
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.business.system.initialize import overlays, updater
from autowsgr.business.system.navigate import goto_page, identify_current_page
from autowsgr.infra.logger import get_logger
from autowsgr.types import GameAPP, PageName
from autowsgr.ui.utils import NavigationError


if TYPE_CHECKING:
    from autowsgr.context import GameContext
    from autowsgr.emulator import AndroidController


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
        _dismiss_overlays(ctx)
        _log.info('[Initialize] 初始化完成, 首页待机')
        return

    # 兜底: SL 强制重启, 只试 1 次 (防死循环)
    _log.warning('[Initialize] 无法回到首页, 执行 SL 强制重启')
    _restart_game(ctx, package)
    if _try_reach_main(ctx):
        _dismiss_overlays(ctx)
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


def _is_on_main_page(ctx: GameContext) -> bool:
    """截图检测当前是否在主页面 (浮层命中也算, 与旧逻辑一致)。"""
    from autowsgr.infra.base.ui.pages.main_page import MainPage

    return bool(MainPage.is_current_page(ctx.ctrl.screenshot()))


# ═══════════════════════════════════════════════════════════════════════════════
# 分支 1/2: 到达主页面
# ═══════════════════════════════════════════════════════════════════════════════


def _try_reach_main(ctx: GameContext) -> bool:
    """尝试到达主页面: 已在 → True; 否则 goto_page (失败重试到超时)。"""
    if identify_current_page(ctx) == PageName.MAIN:
        return True

    deadline = time.monotonic() + _RECOVERY_TIMEOUT
    while time.monotonic() < deadline:
        try:
            goto_page(ctx, PageName.MAIN)
            return True
        except NavigationError:
            time.sleep(_RECOVERY_RETRY_INTERVAL)

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
    _click_enter(ctx)

    # ④ 验证真的到达主页面 (旧代码缺这一步)
    if not _wait_for_main_page(ctx):
        raise TimeoutError(f'点击进入后超时 ({_ENTER_MAIN_TIMEOUT:.0f}s), 未到达主页面')


def _wait_for_start_screen(
    ctx: GameContext, *, timeout: float = _STARTUP_TIMEOUT
) -> bool:
    """轮询等待「点击进入」启动画面出现。"""
    from autowsgr.infra.base.ui.pages.start_screen import StartScreenPage

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if StartScreenPage.is_current_page(ctx.ctrl.screenshot()):
            _log.info('[Initialize] 检测到启动画面')
            return True
        time.sleep(_STARTUP_POLL_INTERVAL)
    return False


def _click_enter(ctx: GameContext) -> None:
    """点击「进入游戏」按钮 — 复用页面控制器 (坐标读 login.yaml)。"""
    from autowsgr.infra.base.ui.pages.start_screen import StartScreenPage

    StartScreenPage(ctx.ctrl).click_enter()


def _wait_for_main_page(ctx: GameContext, *, timeout: float = _ENTER_MAIN_TIMEOUT) -> bool:
    """轮询等待到达主页面 (点击进入后的验证)。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _is_on_main_page(ctx):
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


# ═══════════════════════════════════════════════════════════════════════════════
# 浮层清理
# ═══════════════════════════════════════════════════════════════════════════════


def _dismiss_overlays(ctx: GameContext) -> None:
    """清每日弹窗 (状态挂任务上下文, 日期门控当天零开销)。"""
    state = getattr(ctx, 'overlay_state', None)
    if state is None:
        state = overlays.OverlayState()
        ctx.overlay_state = state
    overlays.handle_daily_overlays(ctx.ctrl, state)
