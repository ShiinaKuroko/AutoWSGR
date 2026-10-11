"""模块功能：把画面解释为出征页标签栏的识别事实。

上层调用：
- application.ui.navigation.page_checker.sortie_checker.checker：读取标签激活事实。

下层依赖：
- common.system.logger：记录识别事实。
- common.vision：提供识别存在入口和识别结果模型。
- page_checker.calibration：加载本模块模板。
- sortie_checker.constants：提供识别区域与模板文件名。

边界：只读取标签激活事实，不执行点击、不组装页面结论、不产出点击坐标。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.page_checker import calibration
from autowsgr.application.ui.navigation.page_checker.sortie_checker import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import ROI, expect_template, expect_template_center


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 识别判定参数 ────────────────────────────────────────────────────────────

# 模板匹配命中阈值。
_TEMPLATE_CONFIDENCE = 0.85


# ── 标签模板表 ──────────────────────────────────────────────────────────────

# 标签名 → (激活态模板, 未激活态模板, 识别区域)；点击前用两张模板任一定位标签。
_TAB_TEMPLATES = {
    'sortie': (
        constants.SORTIE_TAB_TEMPLATE,
        constants.SORTIE_TAB_INACTIVE_TEMPLATE,
        constants.SORTIE_TAB_ROI,
    ),
    'exercise': (
        constants.EXERCISE_TAB_TEMPLATE,
        constants.EXERCISE_TAB_INACTIVE_TEMPLATE,
        constants.EXERCISE_TAB_ROI,
    ),
    'expedition': (
        constants.EXPEDITION_TAB_TEMPLATE,
        constants.EXPEDITION_TAB_INACTIVE_TEMPLATE,
        constants.EXPEDITION_TAB_ROI,
    ),
    'campaign': (
        constants.CAMPAIGN_TAB_TEMPLATE,
        constants.CAMPAIGN_TAB_INACTIVE_TEMPLATE,
        constants.CAMPAIGN_TAB_ROI,
    ),
    'decisive': (
        constants.DECISIVE_TAB_TEMPLATE,
        constants.DECISIVE_TAB_INACTIVE_TEMPLATE,
        constants.DECISIVE_TAB_ROI,
    ),
}


# ── 标签激活事实读取 ────────────────────────────────────────────────────────


def is_sortie_tab_active(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """判断出征标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望该标签不再激活时为真，默认期望它激活。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    return _is_tab_active(
        ctx,
        constants.SORTIE_TAB_TEMPLATE,
        constants.SORTIE_TAB_ROI,
        name='sortie_tab',
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


def is_exercise_tab_active(ctx: ContextHandle) -> bool:
    """判断演习标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        演习标签处于激活态时为真。
    """
    return _is_tab_active(
        ctx,
        constants.EXERCISE_TAB_TEMPLATE,
        constants.EXERCISE_TAB_ROI,
        name='exercise_tab',
    )


def is_expedition_tab_active(ctx: ContextHandle) -> bool:
    """判断远征标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        远征标签处于激活态时为真。
    """
    return _is_tab_active(
        ctx,
        constants.EXPEDITION_TAB_TEMPLATE,
        constants.EXPEDITION_TAB_ROI,
        name='expedition_tab',
    )


def is_campaign_tab_active(ctx: ContextHandle) -> bool:
    """判断战役标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        战役标签处于激活态时为真。
    """
    return _is_tab_active(
        ctx,
        constants.CAMPAIGN_TAB_TEMPLATE,
        constants.CAMPAIGN_TAB_ROI,
        name='campaign_tab',
    )


def is_decisive_tab_active(ctx: ContextHandle) -> bool:
    """判断决战标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        决战标签处于激活态时为真。
    """
    return _is_tab_active(
        ctx,
        constants.DECISIVE_TAB_TEMPLATE,
        constants.DECISIVE_TAB_ROI,
        name='decisive_tab',
    )


def read_tab_center(ctx: ContextHandle, tab: str) -> tuple[float, float] | None:
    """读取出征页某个标签的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        tab: 标签名，取值 sortie / exercise / expedition / campaign / decisive。

    Returns:
        标签模板命中时的归一化中心；未命中时为 None。

    Raises:
        ValueError: 标签名不在本页标签表内。
    """
    templates = _TAB_TEMPLATES.get(tab)
    if templates is None:
        raise ValueError(f'未知的出征标签: {tab!r}')
    active, inactive, roi = templates
    center = expect_template_center(
        ctx,
        template=(
            calibration.load_module_template(
                constants.TEMPLATE_NAMESPACE, active, name=f'{tab}_tab'
            ),
            calibration.load_module_template(
                constants.TEMPLATE_NAMESPACE,
                inactive,
                name=f'{tab}_tab_inactive',
            ),
        ),
        roi=roi,
        confidence=_TEMPLATE_CONFIDENCE,
        attempts=1,
    )
    _log.debug('[UI] 出征标签 → 读标签中心：tab={!r}，center={!r}', tab, center)
    return center


def _is_tab_active(
    ctx: ContextHandle,
    filename: str,
    roi: ROI,
    *,
    name: str,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """按激活态模板判断一个标签是否处于选中状态。"""
    result = expect_template(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            filename,
            name=name,
        ),
        roi=roi,
        confidence=_TEMPLATE_CONFIDENCE,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )
    _log.debug('[UI] 出征标签 → 读激活状态：tab={!r}，active={!r}', name, result.satisfied)
    return result.satisfied
