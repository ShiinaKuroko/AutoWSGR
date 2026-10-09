"""模块功能：编排主页与每日浮窗的识别入口。

上层调用：
- application.ui.navigation：识别当前是否在主页，以及主页上存在的每日浮窗。

下层依赖：
- home_checker.recognition：读取页面与浮窗识别事实。

边界：只编排识别并组装事实，不执行点击、不计算路由、不上报识别错误。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.page_checker.home_checker import recognition


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 主页浮窗事实模型 ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class HomeNewsOverlay:
    """每日公告浮窗的识别事实。

    Attributes:
        matched: 公告浮窗是否在主页上。
        checked: 公告勾选框状态；已勾选为真、未勾选为假、没有读到勾选框时为空。
    """

    matched: bool
    checked: bool | None


# ── 识别入口 ──────────────────────────────────────────────────────────────────────


def check_home_page(ctx: ContextHandle) -> bool:
    """确认当前是否在主页。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        主页模板命中时为真；浮窗遮挡主页模板时为假，由调用方先处理浮窗。
    """
    return recognition.is_home_page_visible(ctx)


def check_home_news_overlay(ctx: ContextHandle) -> HomeNewsOverlay:
    """读取每日公告浮窗事实。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        公告浮窗事实：是否在主页上、勾选框状态。
    """
    matched, checked = recognition.read_news_overlay(ctx)
    state = HomeNewsOverlay(matched=matched, checked=checked)
    _log.debug(
        '[UI] 主页浮窗 → 读公告事实：matched={!r}，checked={!r}',
        state.matched,
        state.checked,
    )
    return state


def check_home_reward_overlay(ctx: ContextHandle) -> bool:
    """确认每日奖励浮窗是否在主页上。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        奖励浮窗存在时为真。
    """
    return recognition.is_reward_overlay_visible(ctx)


def check_home_reward_confirm(ctx: ContextHandle) -> bool:
    """确认每日奖励确认浮窗是否在主页上。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        确认浮窗存在时为真。
    """
    return recognition.is_reward_confirm_visible(ctx)
