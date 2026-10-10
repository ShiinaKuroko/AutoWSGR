"""模块功能：编排出征页五个标签的识别入口。

上层调用：
- application.ui.navigation：确认出征、演习、远征、战役、决战标签当前的激活状态。

下层依赖：
- sortie_checker.recognition：读取标签激活事实。

边界：只编排识别并返回事实，不执行点击、不计算路由、不上报识别错误。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.page_checker.sortie_checker import recognition


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


# ── 识别入口 ────────────────────────────────────────────────────────────────


def check_sortie_page(ctx: ContextHandle) -> bool:
    """确认出征标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        出征标签激活时为真；第一次进入出征页默认落在该标签。
    """
    return recognition.is_sortie_tab_active(ctx)


def check_exercise_page(ctx: ContextHandle) -> bool:
    """确认演习标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        演习标签激活时为真。
    """
    return recognition.is_exercise_tab_active(ctx)


def check_expedition_page(ctx: ContextHandle) -> bool:
    """确认远征标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        远征标签激活时为真。
    """
    return recognition.is_expedition_tab_active(ctx)


def check_campaign_page(ctx: ContextHandle) -> bool:
    """确认战役标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        战役标签激活时为真。
    """
    return recognition.is_campaign_tab_active(ctx)


def check_decisive_page(ctx: ContextHandle) -> bool:
    """确认决战标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        决战标签激活时为真。
    """
    return recognition.is_decisive_tab_active(ctx)


def read_tab_center(ctx: ContextHandle, tab: str) -> tuple[float, float] | None:
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
