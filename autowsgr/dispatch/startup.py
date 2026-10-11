"""模块功能：任务开始前的启动与状态编排入口。

上层调用：
- dispatch.processor：派发任务前确保游戏处于「主页 + 浮层已清」。
- application.runtime.launcher：需要拉起游戏时显式调用。

下层依赖：
- application.ui.navigation：启动流程与页面导航的唯一编排者。

边界：只决定何时启动、何时 SL；不做识别、点击与页面坐标，识别与点击全部由导航器编排。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.errors import ManualRepairRequiredError
from autowsgr.application.ui.navigation.service import NavigationService
from autowsgr.application.ui.navigation.types import (
    ManualUpdateRequiredError,
    NavigationError,
    PageName,
)
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('dispatch.startup')


def ensure_ready(ctx: ContextHandle) -> None:
    """确保游戏处于可以开始任务的状态：主页 + 浮层已清。

    幂等：任意状态进来结果一致；SL 与异常恢复复用同一入口。

    Args:
        ctx: 提供设备服务与任务事实的 dispatch 上下文句柄。

    Raises:
        ManualRepairRequiredError: 游戏需要更新，只能人工处理，SL 无意义。
        NavigationError: SL 之后仍然无法回到主页。
    """
    navigator = NavigationService(ctx)

    # 三种入口状态统一收口；启动失败、区服没选完、回主页失败都走同一套恢复。
    try:
        if not _is_game_running(ctx):
            navigator.ensure_started()
        else:
            _follow_game_display(ctx)
            # 游戏可能停在区服选择页（上次没选完），先把区服选完再回家。
            navigator.ensure_server_selected()
        navigator.navigate_to(PageName.HOME)
    except ManualUpdateRequiredError as error:
        _log.error('[DISPATCH] 启动 → 终止：reason={!r}', str(error))
        raise ManualRepairRequiredError('检测到游戏更新，请手动完成后重试') from error
    except NavigationError as error:
        _log.warning('[DISPATCH] 启动 → 重启：reason={!r}，result=restart', str(error))
        navigator.restart_game()
        navigator.navigate_to(PageName.HOME)


def _follow_game_display(ctx: ContextHandle) -> None:
    """让设备截图跟随游戏所在的显示器。

    多显示器模拟器（如 MuMu 的独立屏）会把游戏放到非默认显示器上，而 scrcpy 默认只镜像
    0 号屏；游戏已经在跑时也必须跟随，否则后续识别全部读的是桌面帧。

    Args:
        ctx: 提供设备服务与配置的 dispatch 上下文句柄。
    """
    package = ctx.runtime.config.account.package_name
    ctx.runtime.ctrl.follow_display(package)


def _is_game_running(ctx: ContextHandle) -> bool:
    """判断游戏进程是否已经在运行。"""
    package = ctx.runtime.config.account.package_name
    return bool(ctx.runtime.ctrl.is_app_running(package))


__all__ = ['ensure_ready']
