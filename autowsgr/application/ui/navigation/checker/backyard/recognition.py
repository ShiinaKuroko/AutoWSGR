"""模块功能：把画面解释为后院主页的识别事实。

上层调用：
- application.ui.navigation.checker.backyard.checker：读取后院主页事实与入口中心。

下层依赖：
- common.system.logger：记录识别事实。
- common.vision：提供识别存在入口与模板中心入口。
- checker.calibration：加载本模块模板。
- backyard.constants：提供识别区域与模板文件名。

边界：只读取识别事实与模板中心，不执行点击、不组装页面结论。
四个二级页的识别各在自己的子包里。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker import calibration
from autowsgr.application.ui.navigation.checker.backyard import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import ROI, expect_template, expect_template_center


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 识别判定参数 ────────────────────────────────────────────────────────────

# 模板匹配命中阈值。
_TEMPLATE_CONFIDENCE = 0.85


# ── 入口表（点击落点用） ────────────────────────────────────────────────────

# 键与 BackyardTarget 枚举名一致；四个入口都在 backyard 根命名空间下。
_ENTRIES: dict[str, tuple[str, ROI]] = {
    'canteen': (constants.CANTEEN_ENTRY_TEMPLATE, constants.CANTEEN_ENTRY_ROI),
    'academy': (constants.ACADEMY_ENTRY_TEMPLATE, constants.ACADEMY_ENTRY_ROI),
    'rank_room': (constants.RANK_ROOM_ENTRY_TEMPLATE, constants.RANK_ROOM_ENTRY_ROI),
    'bath': (constants.BATH_ENTRY_TEMPLATE, constants.BATH_ENTRY_ROI),
}


# ── 识别入口 ────────────────────────────────────────────────────────────────


def read_backyard(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取是否在后院主页。

    后院主页没有专属模板，拿四个入口里的任意一个当身份即可；前识别判到达，
    后识别判离开——进二级页时整页被换掉，入口模板自然消失。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望离开后院主页时为真，默认期望它到达。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    result = expect_template(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.BACKYARD_TEMPLATE,
            name='backyard',
        ),
        roi=constants.BACKYARD_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )
    _log.debug('[UI] 后院主页 → 读识别事实：matched={!r}', result.satisfied)
    return result.satisfied


# ── 模板中心（点击落点） ────────────────────────────────────────────────────


def read_canteen_entry_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取餐厅入口模板命中的中心，供导航器点击。"""
    return _read_entry_center(ctx, 'canteen')


def read_academy_entry_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取学院入口模板命中的中心，供导航器点击。"""
    return _read_entry_center(ctx, 'academy')


def read_rank_room_entry_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取军阶室入口模板命中的中心，供导航器点击。"""
    return _read_entry_center(ctx, 'rank_room')


def read_bath_entry_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取浴室入口模板命中的中心，供导航器点击。"""
    return _read_entry_center(ctx, 'bath')


# ── 私有辅助 ────────────────────────────────────────────────────────────────


def _read_entry_center(ctx: ContextHandle, key: str) -> tuple[float, float] | None:
    """读取某个入口模板命中的中心；未命中时为 None，调用方用静态坐标兜底。"""
    filename, roi = _ENTRIES[key]
    center = expect_template_center(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE, filename, name=f'{key}_entry'
        ),
        roi=roi,
        confidence=_TEMPLATE_CONFIDENCE,
        attempts=1,
    )
    _log.debug('[UI] 后院主页 → 读入口中心：key={!r}，center={!r}', key, center)
    return center
