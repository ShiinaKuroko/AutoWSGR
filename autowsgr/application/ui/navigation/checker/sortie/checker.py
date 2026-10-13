"""模块功能：编排出征页五个标签的识别入口。

上层调用：
- application.ui.navigation：确认出征、演习、远征、战役、决战标签当前的激活状态。

下层依赖：
- sortie.recognition：读取标签激活事实。

边界：只编排识别并返回事实，不执行点击、不计算路由、不上报识别错误。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker.sortie import recognition


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


# ── 识别入口 ────────────────────────────────────────────────────────────────


# 切到这个标签后页面要走一段切换动画；执行器点完标签只确认一次，
# 因此默认给足重试（7 次 × 0.5 秒 ≈ 3.5 秒），动画没走完时继续等。
_TAB_SWITCH_ATTEMPTS = 7
_TAB_SWITCH_INTERVAL_SECONDS = 0.5


def check_sortie_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _TAB_SWITCH_ATTEMPTS,
    interval_seconds: float = _TAB_SWITCH_INTERVAL_SECONDS,
) -> bool:
    """确认出征标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望该标签不再激活时为真，默认期望它激活。
        attempts: 识别次数，默认按标签切换节奏。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真；第一次进入出征页默认落在该标签。
    """
    return recognition.read_sortie_tab(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def check_exercise_page(ctx: ContextHandle) -> bool:
    """确认演习标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        演习标签激活时为真。
    """
    return recognition.read_exercise_tab(ctx)


def check_expedition_page(ctx: ContextHandle) -> bool:
    """确认远征标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        远征标签激活时为真。
    """
    return recognition.read_expedition_tab(ctx)


def check_campaign_page(ctx: ContextHandle) -> bool:
    """确认战役标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        战役标签激活时为真。
    """
    return recognition.read_campaign_tab(ctx)


def check_decisive_page(ctx: ContextHandle) -> bool:
    """确认决战标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        决战标签激活时为真。
    """
    return recognition.read_decisive_tab(ctx)


def read_tab_center(ctx: ContextHandle, tab: str) -> tuple[float, float]:
    """读取出征页某个标签的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        tab: 标签名，取值 sortie / exercise / expedition / campaign / decisive。

    Returns:
        标签模板命中时的归一化中心；未命中时为 None。

    Raises:
        ValueError: 标签名不在本页标签表内。
    """
    return recognition.read_tab_center(ctx, tab)
