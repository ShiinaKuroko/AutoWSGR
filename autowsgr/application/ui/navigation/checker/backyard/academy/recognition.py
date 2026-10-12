"""模块功能：把画面解释为学院二级页的识别事实。

上层调用：
- application.ui.navigation.checker.backyard.academy.checker：读取页面事实。

下层依赖：
- common.system.logger：记录识别事实。
- common.vision：提供识别存在入口。
- checker.calibration：加载本模块模板。
- academy.constants：提供识别区域与模板文件名。

边界：只读取识别事实，不执行点击、不组装页面结论、不产出点击坐标。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker import calibration
from autowsgr.application.ui.navigation.checker.backyard.academy import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import expect_template


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 识别判定参数 ────────────────────────────────────────────────────────────

# 模板匹配命中阈值。
_TEMPLATE_CONFIDENCE = 0.85


# ── 识别入口 ────────────────────────────────────────────────────────────────


def read_academy_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取是否在学院二级页。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望离开该页时为真，默认期望它到达。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    result = expect_template(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.PAGE_TEMPLATE,
            name='academy_page',
        ),
        roi=constants.PAGE_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )
    _log.debug('[UI] 学院二级页 → 读识别事实：matched={!r}', result.satisfied)
    return result.satisfied
