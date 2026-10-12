"""模块功能：编排后院主页与四个二级页的到达确认入口。

上层调用：
- application.ui.navigation：确认后院主页与四个二级页是否到达或离开。

下层依赖：
- backyard.recognition：读取后院识别事实与入口模板中心。

边界：只编排识别并返回结论，不执行点击、不计算路由、不上报识别错误。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker.backyard import recognition


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


# 进后院有较长的切换动画，到达确认给足重试（等效 8 秒缓冲，用户确认不用 sleep）。
_BACKYARD_ENTRY_ATTEMPTS = 8

# 二级页之间的切换走同一套动画，节奏与其余页面一致。
_NAV_CONFIRM_ATTEMPTS = 5
_NAV_CONFIRM_INTERVAL_SECONDS = 1.0


# ── 识别入口 ────────────────────────────────────────────────────────────────


def check_backyard_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _BACKYARD_ENTRY_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认是否在后院主页。

    后院主页没有专属模板，拿四个入口里的任意一个当身份；前识别判到达，后识别判离开。
    离开判定天然成立：进二级页时整页被换掉，入口模板自然消失。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望离开后院主页时为真，默认期望它到达。
        attempts: 识别次数，默认按进后院的节奏。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return recognition.read_backyard(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def check_canteen_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认是否在餐厅二级页。"""
    return recognition.read_canteen_page(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def check_academy_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认是否在学院二级页。"""
    return recognition.read_academy_page(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def check_rank_room_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认是否在军阶室二级页。"""
    return recognition.read_rank_room_page(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def check_bath_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认是否在浴室二级页。"""
    return recognition.read_bath_page(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


# ── 模板中心 ────────────────────────────────────────────────────────────────


def read_canteen_entry_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取餐厅入口模板命中的中心，供导航器点击。"""
    return recognition.read_canteen_entry_center(ctx)


def read_academy_entry_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取学院入口模板命中的中心，供导航器点击。"""
    return recognition.read_academy_entry_center(ctx)


def read_rank_room_entry_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取军阶室入口模板命中的中心，供导航器点击。"""
    return recognition.read_rank_room_entry_center(ctx)


def read_bath_entry_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取浴室入口模板命中的中心，供导航器点击。"""
    return recognition.read_bath_entry_center(ctx)


__all__ = [
    'check_academy_page',
    'check_backyard_page',
    'check_bath_page',
    'check_canteen_page',
    'check_rank_room_page',
    'read_academy_entry_center',
    'read_bath_entry_center',
    'read_canteen_entry_center',
    'read_rank_room_entry_center',
]
