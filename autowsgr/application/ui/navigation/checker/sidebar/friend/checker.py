"""模块功能：编排好友页面的到达确认入口。

上层调用：
- application.ui.navigation：确认好友页面是否到达或离开。

下层依赖：
- friend.recognition：读取好友页面的识别事实。

边界：只编排识别并返回结论，不执行点击、不计算路由、不上报识别错误。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker.sidebar.friend import recognition


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


# 导航确认节奏：从侧边栏切页要走完转场动画，识别不到就重试。
_NAV_CONFIRM_ATTEMPTS = 5
_NAV_CONFIRM_INTERVAL_SECONDS = 1.0


# ── 识别入口 ────────────────────────────────────────────────────────────────


def check_friend_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认好友页面是否在前台。

    前识别判好友页面出现，后识别判它离开。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望好友页面离开时为真，默认期望它出现。
        attempts: 识别次数，默认按导航确认节奏。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return recognition.read_friend_page(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


__all__ = ['check_friend_page']
