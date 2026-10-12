"""模块功能：把画面解释为好友页面的识别事实。

上层调用：
- application.ui.navigation.checker.sidebar.friend.checker：读取好友页面事实。

下层依赖：
- common.system.logger：记录识别事实。
- common.vision：提供识别存在入口。
- checker.calibration：加载本模块模板。
- friend.constants：提供识别区域与模板文件名。

边界：只读取识别事实，不执行点击、不组装页面结论、不产出点击坐标。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker import calibration
from autowsgr.application.ui.navigation.checker.sidebar.friend import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import expect_template


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 识别判定参数 ────────────────────────────────────────────────────────────

# 模板匹配命中阈值。
_TEMPLATE_CONFIDENCE = 0.85


# ── 识别入口 ────────────────────────────────────────────────────────────────


def read_friend_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取好友页面是否在前台。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望好友页面不在时为真，默认期望它在。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    result = expect_template(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.ADD_TAB_TEMPLATE,
            name='friend_add_tab',
        ),
        roi=constants.ADD_TAB_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )
    _log.debug('[UI] 好友页面 → 读识别事实：matched={!r}', result.satisfied)
    return result.satisfied
