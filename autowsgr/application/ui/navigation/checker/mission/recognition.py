"""模块功能：把画面解释为任务页的识别事实。

上层调用：
- application.ui.navigation.checker.mission.checker：读取任务页与领奖相关事实。

下层依赖：
- common.system.logger：记录识别事实。
- common.vision：提供识别存在入口。
- checker.calibration：加载本模块模板。
- mission.constants：提供识别区域与模板文件名。

边界：只读取识别事实，不执行点击、不组装页面结论、不产出点击坐标。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker import calibration
from autowsgr.application.ui.navigation.checker.mission import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import ROI, expect_template


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 识别判定参数 ────────────────────────────────────────────────────────────

# 模板匹配命中阈值。
_TEMPLATE_CONFIDENCE = 0.85


# ── 识别入口 ────────────────────────────────────────────────────────────────


def read_mission_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取是否在任务页。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望离开任务页时为真，默认期望它在。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return _read_template(
        ctx,
        constants.ALL_TAB_TEMPLATE,
        constants.ALL_TAB_ROI,
        name='mission_all_tab',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
        note='\u4efb\u52a1\u9875',
    )


def read_claim_all_button(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取右下角「全部领取」按钮是否出现。

    按钮不遮挡任务页，因此它不是独立页面；调用方按「先问再做」使用本入口。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望按钮不在时为真，默认期望它在。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return _read_template(
        ctx,
        constants.CLAIM_ALL_BUTTON_TEMPLATE,
        constants.CLAIM_ALL_BUTTON_ROI,
        name='mission_claim_all',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
        note='\u5168\u90e8\u9886\u53d6\u6309\u94ae',
    )


def read_reward_confirm_button(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取「获得」浮窗里的「确认」按钮是否出现。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望确认浮窗不在时为真，默认期望它在。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return _read_template(
        ctx,
        constants.REWARD_CONFIRM_BUTTON_TEMPLATE,
        constants.REWARD_CONFIRM_BUTTON_ROI,
        name='mission_reward_confirm',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
        note='\u83b7\u5f97\u786e\u8ba4\u6309\u94ae',
    )


# ── 私有辅助 ────────────────────────────────────────────────────────────────


def _read_template(
    ctx: ContextHandle,
    filename: str,
    roi: ROI,
    *,
    name: str,
    absent: bool,
    attempts: int,
    interval_seconds: float,
    note: str,
) -> bool:
    """按模板读取一个任务页事实。"""
    result = expect_template(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE, filename, name=name
        ),
        roi=roi,
        confidence=_TEMPLATE_CONFIDENCE,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )
    _log.debug('[UI] 任务页 → 读识别事实：name={!r}，matched={!r}', name, result.satisfied)
    return result.satisfied
