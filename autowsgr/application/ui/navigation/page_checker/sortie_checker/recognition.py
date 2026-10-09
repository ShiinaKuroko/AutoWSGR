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

from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import ROI, expect_template
from autowsgr.application.ui.navigation.page_checker import calibration
from autowsgr.application.ui.navigation.page_checker.sortie_checker import constants


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 识别判定参数 ────────────────────────────────────────────────────────────

# 模板匹配命中阈值。
_TEMPLATE_CONFIDENCE = 0.85


# ── 标签激活事实读取 ────────────────────────────────────────────────────────


def is_sortie_tab_active(ctx: ContextHandle) -> bool:
    """判断出征标签是否激活。"""
    return _is_tab_active(
        ctx,
        constants.SORTIE_TAB_TEMPLATE,
        constants.SORTIE_TAB_ROI,
        name='sortie_tab',
    )


def is_exercise_tab_active(ctx: ContextHandle) -> bool:
    """判断演习标签是否激活。"""
    return _is_tab_active(
        ctx,
        constants.EXERCISE_TAB_TEMPLATE,
        constants.EXERCISE_TAB_ROI,
        name='exercise_tab',
    )


def is_expedition_tab_active(ctx: ContextHandle) -> bool:
    """判断远征标签是否激活。"""
    return _is_tab_active(
        ctx,
        constants.EXPEDITION_TAB_TEMPLATE,
        constants.EXPEDITION_TAB_ROI,
        name='expedition_tab',
    )


def is_campaign_tab_active(ctx: ContextHandle) -> bool:
    """判断战役标签是否激活。"""
    return _is_tab_active(
        ctx,
        constants.CAMPAIGN_TAB_TEMPLATE,
        constants.CAMPAIGN_TAB_ROI,
        name='campaign_tab',
    )


def is_decisive_tab_active(ctx: ContextHandle) -> bool:
    """判断决战标签是否激活。"""
    return _is_tab_active(
        ctx,
        constants.DECISIVE_TAB_TEMPLATE,
        constants.DECISIVE_TAB_ROI,
        name='decisive_tab',
    )


def _is_tab_active(ctx: ContextHandle, filename: str, roi: ROI, *, name: str) -> bool:
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
    )
    _log.debug('[UI] 出征标签 → 读激活状态：tab={!r}，active={!r}', name, result.satisfied)
    return result.satisfied
