"""模块功能：把画面解释为改造页面的识别事实。

上层调用：
- application.ui.navigation.checker.sidebar.intensify.checker：读取标签激活事实。

下层依赖：
- common.system.logger：记录识别事实。
- common.vision：提供识别存在入口。
- checker.calibration：加载本模块模板。
- intensify.constants：提供识别区域与模板文件名。

边界：只读取标签激活事实，不执行点击、不组装页面结论、不产出点击坐标。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker import calibration
from autowsgr.application.ui.navigation.checker.sidebar.intensify import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import ROI, expect_template


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 识别判定参数 ────────────────────────────────────────────────────────────

# 模板匹配命中阈值。
_TEMPLATE_CONFIDENCE = 0.85


# ── 识别入口 ────────────────────────────────────────────────────────────────


def read_intensify_tab(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取改造页「强化」标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望该标签未激活时为真，默认期望它激活。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return _read_tab(
        ctx,
        constants.INTENSIFY_TAB_TEMPLATE,
        constants.INTENSIFY_TAB_ROI,
        name='intensify_tab',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def read_remold_tab(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取改造页「改造」标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望该标签未激活时为真，默认期望它激活。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return _read_tab(
        ctx,
        constants.REMOLD_TAB_TEMPLATE,
        constants.REMOLD_TAB_ROI,
        name='remold_tab',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def read_skill_tab(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取改造页「技能」标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望该标签未激活时为真，默认期望它激活。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return _read_tab(
        ctx,
        constants.SKILL_TAB_TEMPLATE,
        constants.SKILL_TAB_ROI,
        name='skill_tab',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


# ── 私有辅助 ────────────────────────────────────────────────────────────────


def _read_tab(
    ctx: ContextHandle,
    filename: str,
    roi: ROI,
    *,
    name: str,
    absent: bool,
    attempts: int,
    interval_seconds: float,
) -> bool:
    """按模板读取一个标签的激活事实。"""
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
    _log.debug('[UI] 改造页面 → 读标签激活事实：name={!r}，matched={!r}', name, result.satisfied)
    return result.satisfied
