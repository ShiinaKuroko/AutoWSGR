"""模块功能：把画面解释为侧边栏的识别事实。

上层调用：
- application.ui.navigation.checker.sidebar.checker：读取侧边栏与二级菜单事实。

下层依赖：
- common.system.logger：记录识别事实。
- common.vision：提供识别存在入口。
- checker.calibration：加载本模块模板。
- sidebar.constants：提供识别区域与模板文件名。

边界：只读取识别事实，不执行点击、不组装页面结论、不产出点击坐标。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker import calibration
from autowsgr.application.ui.navigation.checker.sidebar import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import ROI, expect_template


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 识别判定参数 ────────────────────────────────────────────────────────────

# 模板匹配命中阈值。
_TEMPLATE_CONFIDENCE = 0.85


# ── 识别入口 ────────────────────────────────────────────────────────────────


def read_sidebar(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取侧边栏是否展开。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望侧边栏收起时为真，默认期望它展开。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return _read_template(
        ctx,
        constants.SIDEBAR_MAIN_TEMPLATE,
        constants.SIDEBAR_MAIN_ROI,
        name='sidebar_main',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def read_build_submenu(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取建造二级菜单是否弹出。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望二级菜单收起时为真，默认期望它弹出。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return _read_template(
        ctx,
        constants.BUILD_SUBMENU_TEMPLATE,
        constants.BUILD_SUBMENU_ROI,
        name='build_submenu',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def read_intensify_submenu(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取强化二级菜单是否弹出。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望二级菜单收起时为真，默认期望它弹出。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return _read_template(
        ctx,
        constants.INTENSIFY_SUBMENU_TEMPLATE,
        constants.INTENSIFY_SUBMENU_ROI,
        name='intensify_submenu',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
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
) -> bool:
    """按模板读取一个侧边栏事实。"""
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
    _log.debug('[UI] 侧边栏 → 读识别事实：name={!r}，matched={!r}', name, result.satisfied)
    return result.satisfied
