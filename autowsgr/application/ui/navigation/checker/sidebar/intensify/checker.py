"""模块功能：编排改造页各标签的到达确认入口。

上层调用：
- application.ui.navigation：确认改造页是否到达，以及切换标签后是否落在目标标签。

下层依赖：
- intensify.recognition：读取标签激活事实。

边界：只编排识别并返回结论，不执行点击、不计算路由、不上报识别错误。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker.sidebar.intensify import recognition


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


# 导航确认节奏：切换标签要走完切换动画，识别不到就重试。
_NAV_CONFIRM_ATTEMPTS = 5
_NAV_CONFIRM_INTERVAL_SECONDS = 1.0


# ── 识别入口 ────────────────────────────────────────────────────────────────


def check_intensify_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认是否在改造页的默认标签上。

    改造页默认落在「强化」标签，因此页面身份用它表达；前识别判到达，后识别判离开。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望离开改造页时为真，默认期望它到达。
        attempts: 识别次数，默认按导航确认节奏。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return recognition.read_intensify_tab(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def check_remold_tab(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认改造页是否切到了「改造」标签。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望该标签未激活时为真，默认期望它激活。
        attempts: 识别次数，默认按导航确认节奏。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return recognition.read_remold_tab(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def check_skill_tab(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认改造页是否切到了「技能」标签。

    Args:
        ctx: 提供设备和截图事实的 dispatch 上下文句柄。
        absent: 期望该标签未激活时为真，默认期望它激活。
        attempts: 识别次数，默认按导航确认节奏。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return recognition.read_skill_tab(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


__all__ = ['check_intensify_page', 'check_remold_tab', 'check_skill_tab']
