"""模块功能：检测和消除母港主页上的登录、签到及活动浮层。

上层调用：
- application.ui.controller.home.page：在页面导航前读取并消除浮层。
- application.ui.controller.home.event_nav：处理活动入口点击后的浮层。
- application.runtime.initialize.overlays：执行每日浮层处理。
- testing.infra.ui.pages.main_page：验证浮层检测和签到确认流程。

下层依赖：
- application.ui.controller.home.constants：提供浮层点击坐标和像素签名。
- common.ui.interaction：处理签到确认弹窗。
- common.vision：匹配浮层模板和像素签名。
"""

from __future__ import annotations

import enum
import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import ImageChecker, PixelChecker
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.device import AndroidController


_log = get_logger('ui')


# ── 浮层类型 ──────────────────────────────────────────────────────────────────


class OverlayKind(enum.Enum):
    """母港主页可出现的浮层类型。"""

    NEWS = '新闻公告'
    SIGN = '每日签到'
    BOOKING = '活动预约'
    USER_INFO = '提督信息'


_SIGN_CONFIRM_MAX: int = 2
"""每日签到最多处理的确认弹窗段数 (领取确认 + 可能的奖励确认)。"""

_SIGN_CONFIRM_WAIT: float = 1.0
"""两段确认之间的等待时间 (秒) — 奖励确认弹窗需几秒才出现。"""

_SIGN_CONFIRM_TIMEOUT: float = 8.0
"""等待确认弹窗出现的最大时限 (秒)。"""


# ── 浮层读取 ──────────────────────────────────────────────────────────────────


def read_overlay(screen: np.ndarray) -> OverlayKind | None:
    """读取截图中的母港浮层类型。

    按优先级依次检测: NEWS → SIGN → BOOKING → USER_INFO。

    Args:
        screen: RGB 截图，形状为 (H, W, 3)。

    Returns:
        检测到的浮层类型；没有已知浮层时返回 None。
    """
    page = Templates.MainPage
    if ImageChecker.template_exists(screen, page.NEWS, confidence=0.85):
        _log.debug('[UI] 检测到浮层: 新闻公告')
        return OverlayKind.NEWS
    if ImageChecker.template_exists(screen, page.SIGN, confidence=0.85):
        _log.debug('[UI] 检测到浮层: 每日签到')
        return OverlayKind.SIGN
    if ImageChecker.template_exists(screen, page.BOOKING, confidence=0.85):
        _log.debug('[UI] 检测到浮层: 活动预约')
        return OverlayKind.BOOKING
    if ImageChecker.template_exists(screen, page.USER_INFO, confidence=0.85):
        _log.debug('[UI] 检测到浮层: 提督信息')
        return OverlayKind.USER_INFO
    return None


# ── 浮层消除 ──────────────────────────────────────────────────────────────────


def dismiss_news(ctrl: AndroidController, screen: np.ndarray | None = None) -> None:
    """关闭新闻公告浮层。

    Args:
        ctrl: 当前游戏设备控制器。
        screen: 可复用的当前截图；未提供时由控制器获取。
    """
    if screen is None:
        screen = ctrl.screenshot()

    not_show = PixelChecker.check_signature(
        screen,
        constants.NEWS_NOT_SHOW_SIGNATURE,
    ).matched
    if not not_show:
        _log.info('[UI] 新闻公告: 勾选「不再显示」')
        ctrl.click(*constants.DISMISS_POSITIONS['news_not_show'])
        time.sleep(0.3)

    _log.info('[UI] 新闻公告: 关闭')
    ctrl.click(*constants.DISMISS_POSITIONS['news_close'])


def dismiss_sign(ctrl: AndroidController) -> None:
    """关闭每日签到浮层 (领取奖励 + 处理确认弹窗)。

    签到奖励流程可能包含连续两段确认弹窗:
    1. 点「领取奖励」后弹出「获得 xx」确认弹窗 → 点确认
    2. 部分版本点确认后还有「奖励确认」二级弹窗 → 有则再点

    第一次确认必须点击 (领取后必有), 第二次确认可选 (等不到就直接收尾)。

    Args:
        ctrl: 当前游戏设备控制器。
    """
    from autowsgr.common.ui.interaction import confirm_operation

    _log.info('[UI] 每日签到: 领取奖励')
    ctrl.click(*constants.DISMISS_POSITIONS['sign_confirm'])
    # 第一段确认: 领取后必有, 等待出现并点击 (超时未出现则视为异常)
    confirm_operation(ctrl, must_confirm=True, timeout=_SIGN_CONFIRM_TIMEOUT)
    # 第二段确认: 等待几秒, 若还有「奖励确认」弹窗则继续点, 直到画面干净
    for _ in range(_SIGN_CONFIRM_MAX - 1):
        time.sleep(_SIGN_CONFIRM_WAIT)
        if not confirm_operation(ctrl, must_confirm=False, timeout=_SIGN_CONFIRM_TIMEOUT):
            return
        _log.info('[UI] 每日签到: 二次确认已点击')


def dismiss_booking(ctrl: AndroidController) -> None:
    """关闭活动预约浮层。

    Args:
        ctrl: 当前游戏设备控制器。
    """
    _log.info('[UI] 活动预约: 关闭')
    ctrl.click(*constants.DISMISS_POSITIONS['booking'])
    time.sleep(1.0)
    # 二次确认 — 若仍未返回主页面则再点一次
    screen = ctrl.screenshot()
    if not ImageChecker.template_exists(screen, Templates.MainPage.MAIN, confidence=0.85):
        _log.warning('[UI] 活动预约: 首次关闭未生效，重试')
        ctrl.click(*constants.DISMISS_POSITIONS['booking'])
        time.sleep(1.0)


def dismiss_user_info(ctrl: AndroidController) -> None:
    """关闭提督信息浮层 (全屏个人资料)。

    Args:
        ctrl: 当前游戏设备控制器。
    """
    _log.info('[UI] 提督信息: 关闭')
    ctrl.click(*constants.DISMISS_POSITIONS['user_info_close'])
    time.sleep(0.5)


def dismiss_overlay(ctrl: AndroidController, overlay: OverlayKind) -> None:
    """按浮层类型执行对应的关闭动作。

    Args:
        ctrl: 当前游戏设备控制器。
        overlay: 当前已识别的母港浮层类型。

    Raises:
        ValueError: overlay 不是支持的浮层类型。
    """
    match overlay:
        case OverlayKind.NEWS:
            dismiss_news(ctrl)
        case OverlayKind.SIGN:
            dismiss_sign(ctrl)
        case OverlayKind.BOOKING:
            dismiss_booking(ctrl)
        case OverlayKind.USER_INFO:
            dismiss_user_info(ctrl)
        case _:
            raise ValueError(f'未知浮层类型: {overlay}')
