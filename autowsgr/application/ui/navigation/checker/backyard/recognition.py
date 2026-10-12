"""模块功能：把画面解释为后院的识别事实。

上层调用：
- application.ui.navigation.checker.backyard.checker：读取后院主页与四个二级页的事实。

下层依赖：
- common.system.logger：记录识别事实。
- common.vision：提供识别存在入口与模板中心入口。
- checker.calibration：加载本模块模板。
- backyard.constants：提供识别区域、模板文件名与命名空间。

边界：只读取识别事实与模板中心，不执行点击、不组装页面结论。
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


# ── 二级页表 ────────────────────────────────────────────────────────────────

# 每项是 (命名空间, 模板文件名, 识别区域)；键与 _ENTRIES 一致。
_PAGES: dict[str, tuple[str, str, ROI]] = {
    'canteen': (
        constants.CANTEEN_PAGE_NAMESPACE,
        constants.CANTEEN_PAGE_TEMPLATE,
        constants.CANTEEN_PAGE_ROI,
    ),
    'academy': (
        constants.ACADEMY_PAGE_NAMESPACE,
        constants.ACADEMY_PAGE_TEMPLATE,
        constants.ACADEMY_PAGE_ROI,
    ),
    'rank_room': (
        constants.RANK_ROOM_PAGE_NAMESPACE,
        constants.RANK_ROOM_PAGE_TEMPLATE,
        constants.RANK_ROOM_PAGE_ROI,
    ),
    'bath': (
        constants.BATH_PAGE_NAMESPACE,
        constants.BATH_PAGE_TEMPLATE,
        constants.BATH_PAGE_ROI,
    ),
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
    return _read_template(
        ctx,
        constants.TEMPLATE_NAMESPACE,
        constants.BACKYARD_TEMPLATE,
        constants.BACKYARD_ROI,
        name='backyard',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def read_canteen_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取是否在餐厅二级页。"""
    return _read_page(
        ctx,
        'canteen',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def read_academy_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取是否在学院二级页。"""
    return _read_page(
        ctx,
        'academy',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def read_rank_room_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取是否在军阶室二级页。"""
    return _read_page(
        ctx,
        'rank_room',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def read_bath_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """读取是否在浴室二级页。"""
    return _read_page(
        ctx,
        'bath',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


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


def _read_template(
    ctx: ContextHandle,
    namespace: str,
    filename: str,
    roi: ROI,
    *,
    name: str,
    absent: bool,
    attempts: int,
    interval_seconds: float,
) -> bool:
    """按模板读取一个后院事实。"""
    result = expect_template(
        ctx,
        template=calibration.load_module_template(namespace, filename, name=name),
        roi=roi,
        confidence=_TEMPLATE_CONFIDENCE,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )
    _log.debug('[UI] 后院 → 读识别事实：name={!r}，matched={!r}', name, result.satisfied)
    return result.satisfied


def _read_page(
    ctx: ContextHandle,
    key: str,
    *,
    absent: bool,
    attempts: int,
    interval_seconds: float,
) -> bool:
    """按模板读取一个二级页的身份事实。"""
    namespace, filename, roi = _PAGES[key]
    return _read_template(
        ctx,
        namespace,
        filename,
        roi,
        name=f'{key}_page',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


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
    _log.debug('[UI] 后院 → 读入口中心：key={!r}，center={!r}', key, center)
    return center
