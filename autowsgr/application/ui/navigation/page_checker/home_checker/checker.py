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

from autowsgr.application.ui.navigation.page_checker.home_checker import recognition
from autowsgr.common.system.logger import get_logger


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


# 导航确认节奏：从登录页进入要等登录动画与加载，因此给足重试。
_NAV_CONFIRM_ATTEMPTS = 30
_NAV_CONFIRM_INTERVAL_SECONDS = 1.0


def check_home_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _NAV_CONFIRM_ATTEMPTS,
    interval_seconds: float = _NAV_CONFIRM_INTERVAL_SECONDS,
) -> bool:
    """确认当前是否在「没有每日浮窗的主页」上。

    主页上有每日浮窗时不算到达主页：三个浮窗各自有页面身份，先走浮窗链把它们清掉，
    最后回到这里确认。后识别（`absent=True`）只看主页模板，不受浮窗影响。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望主页标志消失时为真，默认期望它出现。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        主页模板命中、且前识别时三个每日浮窗都不在时为真。
    """
    if not recognition.is_home_page_visible(
        ctx,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    ):
        return False
    # 后识别只判模板消失，浮窗无关。
    if absent:
        return True
    # 前识别：还有浮窗就交给浮窗页表达，这里不算到达主页。
    news_matched, _ = recognition.read_news_overlay(ctx)
    if news_matched:
        return False
    return not (
        recognition.is_reward_overlay_visible(ctx) or recognition.is_reward_confirm_visible(ctx)
    )


def check_home_news_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """确认主页上是否有每日公告浮窗，供整页身份使用。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望公告浮窗不在时为真，默认期望它在。
        attempts: 识别次数；浮窗识别只看当前一帧，保留参数只为与其他整页入口签名一致。
        interval_seconds: 两次识别之间的等待秒数，同上。

    Returns:
        断言满足时为真。
    """
    matched = check_home_news_overlay(ctx).matched
    return (not matched) if absent else matched


def check_home_reward_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """确认主页上「当前这一层」是每日奖励浮窗，供整页身份使用。

    领取后确认浮窗会叠在奖励浮窗上面，此时这一层已经是确认浮窗，奖励浮窗不再算作当前页；
    不排除的话「每日奖励 → 每日奖励确认」这一步的离开确认永远不成立。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望奖励浮窗不在当前层时为真，默认期望这一层就是它。
        attempts: 识别次数；浮窗识别只看当前一帧，保留参数只为与其他整页入口签名一致。
        interval_seconds: 两次识别之间的等待秒数，同上。

    Returns:
        断言满足时为真。
    """
    matched = check_home_reward_overlay(ctx) and not check_home_reward_confirm(ctx)
    return (not matched) if absent else matched


def check_home_reward_confirm_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """确认主页上是否有每日奖励确认浮窗，供整页身份使用。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望确认浮窗不在时为真，默认期望它在。
        attempts: 识别次数；浮窗识别只看当前一帧，保留参数只为与其他整页入口签名一致。
        interval_seconds: 两次识别之间的等待秒数，同上。

    Returns:
        断言满足时为真。
    """
    matched = check_home_reward_confirm(ctx)
    return (not matched) if absent else matched


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


def read_news_checkbox_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取每日公告勾选框的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        勾选框模板命中时的归一化中心；未命中时为 None。
    """
    return recognition.read_news_checkbox_center(ctx)


def read_reward_claim_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取每日奖励领取按钮的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        领取按钮模板命中时的归一化中心；未命中时为 None。
    """
    return recognition.read_reward_claim_center(ctx)


def read_reward_confirm_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取每日奖励确认按钮的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        确认按钮模板命中时的归一化中心；未命中时为 None。
    """
    return recognition.read_reward_confirm_center(ctx)
