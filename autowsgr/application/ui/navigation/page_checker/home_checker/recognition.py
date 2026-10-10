"""模块功能：把画面解释为主页与每日浮窗的识别事实。

上层调用：
- application.ui.navigation.page_checker.home_checker.checker：读取页面识别事实。

下层依赖：
- common.system.logger：记录识别事实。
- common.vision：提供前识别入口和识别结果模型。
- page_checker.calibration：加载本模块模板。
- home_checker.constants：提供识别区域与模板文件名。

边界：只读取画面事实，不执行点击、不组装页面结论、不产出点击坐标。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.page_checker import calibration
from autowsgr.application.ui.navigation.page_checker.home_checker import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import expect_template, expect_template_center


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 识别判定参数 ────────────────────────────────────────────────────────────────────

# 模板匹配命中阈值。
_TEMPLATE_CONFIDENCE = 0.85


# ── 页面事实读取 ────────────────────────────────────────────────────────────────────


def is_home_page_visible(ctx: ContextHandle) -> bool:
    """判断主页模板是否可见。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        主页模板命中时为真。
    """
    result = expect_template(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.HOME_MAIN_TEMPLATE,
            name='home_main',
        ),
        roi=constants.HOME_MAIN_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
    )
    _log.debug('[UI] 主页识别 → 查主页模板：visible={!r}', result.satisfied)
    return result.satisfied


def read_news_overlay(ctx: ContextHandle) -> tuple[bool, bool | None]:
    """读取每日公告浮窗事实。

    一次识别同时匹配公告文字与勾选框，因此浮窗状态和勾选状态来自同一帧。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        二元组：公告浮窗是否在；勾选框状态（已勾选为真、未勾选为假、没读到为空）。
    """
    templates = (
        calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.NEWS_TEXT_TEMPLATE,
            name='home_news_text',
        ),
        calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.NEWS_CHECKED_TEMPLATE,
            name='home_news_checked',
        ),
        calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.NEWS_UNCHECKED_TEMPLATE,
            name='home_news_unchecked',
        ),
    )
    rois = (
        constants.NEWS_TEXT_ROI,
        constants.NEWS_CHECKBOX_ROI,
        constants.NEWS_CHECKBOX_ROI,
    )
    result = expect_template(
        ctx,
        template=templates,
        roi=rois,
        confidence=_TEMPLATE_CONFIDENCE,
    )
    text_match, checked_match, unchecked_match = result.observation
    # 勾选框只属于公告浮窗，因此任一模板命中都说明公告浮窗仍在主页上。
    matched = text_match.matched or checked_match.matched or unchecked_match.matched
    checked: bool | None = None
    if checked_match.matched:
        checked = True
    elif unchecked_match.matched:
        checked = False
    _log.debug(
        '[UI] 主页识别 → 读公告浮窗：matched={!r}，checked={!r}，text_matched={!r}',
        matched,
        checked,
        text_match.matched,
    )
    return matched, checked


def is_reward_overlay_visible(ctx: ContextHandle) -> bool:
    """判断每日奖励浮窗是否在主页上。

    奖励文字或领取按钮任一命中即算浮窗存在。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        浮窗存在时为真。
    """
    templates = (
        calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.REWARD_TEXT_TEMPLATE,
            name='home_reward_text',
        ),
        calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.REWARD_CLAIM_TEMPLATE,
            name='home_reward_claim',
        ),
    )
    rois = (constants.REWARD_TEXT_ROI, constants.REWARD_CLAIM_BUTTON_ROI)
    result = expect_template(
        ctx,
        template=templates,
        roi=rois,
        confidence=_TEMPLATE_CONFIDENCE,
    )
    _log.debug('[UI] 主页识别 → 读奖励浮窗：visible={!r}', result.satisfied)
    return result.satisfied


def is_reward_confirm_visible(ctx: ContextHandle) -> bool:
    """判断每日奖励确认浮窗是否在主页上。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        确认浮窗存在时为真。
    """
    result = expect_template(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.REWARD_CONFIRM_TEMPLATE,
            name='home_reward_confirm',
        ),
        roi=constants.REWARD_CONFIRM_BUTTON_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
    )
    _log.debug('[UI] 主页识别 → 读奖励确认浮窗：visible={!r}', result.satisfied)
    return result.satisfied


def read_news_checkbox_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取每日公告勾选框的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        勾选框模板命中时的归一化中心；未命中时为 None。
    """
    templates = (
        calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.NEWS_CHECKED_TEMPLATE,
            name='home_news_checked',
        ),
        calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.NEWS_UNCHECKED_TEMPLATE,
            name='home_news_unchecked',
        ),
    )
    center = expect_template_center(
        ctx,
        template=templates,
        roi=constants.NEWS_CHECKBOX_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
    )
    _log.debug('[UI] 主页识别 → 读勾选框中心：center={!r}', center)
    return center


def read_reward_claim_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取每日奖励领取按钮的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        领取按钮模板命中时的归一化中心；未命中时为 None。
    """
    center = expect_template_center(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.REWARD_CLAIM_TEMPLATE,
            name='home_reward_claim',
        ),
        roi=constants.REWARD_CLAIM_BUTTON_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
    )
    _log.debug('[UI] 主页识别 → 读领取按钮中心：center={!r}', center)
    return center


def read_reward_confirm_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取每日奖励确认按钮的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        确认按钮模板命中时的归一化中心；未命中时为 None。
    """
    center = expect_template_center(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.REWARD_CONFIRM_TEMPLATE,
            name='home_reward_confirm',
        ),
        roi=constants.REWARD_CONFIRM_BUTTON_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
    )
    _log.debug('[UI] 主页识别 → 读确认按钮中心：center={!r}', center)
    return center
