"""模块功能：编排任务页与其领奖浮窗的到达确认入口。

上层调用：
- application.ui.navigation：确认任务页与「获得」浮窗是否到达或离开，
  以及「全部领取」按钮是否出现。

下层依赖：
- mission.recognition：读取任务页与领奖相关事实。

边界：只编排识别并返回结论，不执行点击、不计算路由、不上报识别错误。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker.mission import recognition


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


# 导航确认节奏：进任务页和弹浮窗都要走完转场，识别不到就重试。
_NAV_CONFIRM_ATTEMPTS = 5
_NAV_CONFIRM_INTERVAL_SECONDS = 1.0


# ── 识别入口 ────────────────────────────────────────────────────────────────


def check_mission_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认是否在任务页。

    任务页默认落在「全部」页签，因此页面身份用它表达；前识别判到达，后识别判离开。
    浮窗弹出时任务页仍在背后，页签可见，因此这个判断在浮窗期间同样成立。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望离开任务页时为真，默认期望它到达。
        attempts: 识别次数，默认按导航确认节奏。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return recognition.read_mission_page(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def check_claim_all_button(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """确认「全部领取」按钮是否出现。

    按钮只在有奖励可领时出现在右下角，且不遮挡任务页，所以它不是页面：
    调用方按「先问再做」使用——不在就什么都不做，避免空点。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望按钮不在时为真，默认期望它在。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return recognition.read_claim_all_button(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def check_mission_reward_confirm(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认「获得」浮窗是否弹出。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望确认浮窗不在时为真，默认期望它弹出。
        attempts: 识别次数，默认按导航确认节奏。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return recognition.read_reward_confirm_button(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


__all__ = [
    'check_claim_all_button',
    'check_mission_page',
    'check_mission_reward_confirm',
]
