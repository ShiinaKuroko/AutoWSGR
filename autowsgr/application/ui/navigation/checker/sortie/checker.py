"""模块功能：确认出征页五个标签的激活状态。

上层调用：
- application.ui.navigation：确认出征、演习、远征、战役、决战标签当前的激活状态，
  并读取标签中心。

下层依赖：
- application.vision：读取模板事实。

边界：只做识别并返回结论，不执行点击、不计算路由、不上报识别错误。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.template import load_ui_template
from autowsgr.common.vision import ROI, Template, expect_template, expect_template_center


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


# ── 识别数据 ────────────────────────────────────────────────────────────────

# 本模块在 UI 模板根下的命名空间。
TEMPLATE_NAMESPACE = 'navigation/checker/sortie'

# 五个标签的激活态与未激活态模板；目录小写、文件名全大写。
# 只保留激活态模板：前识别命中即激活，后识别（absent）命中即未激活，不必再存一套未激活模板。
SORTIE_TAB_TEMPLATE = 'SORTIE_SORTIE_TAB_720P.png'
EXERCISE_TAB_TEMPLATE = 'SORTIE_EXERCISE_TAB_720P.png'
EXPEDITION_TAB_TEMPLATE = 'SORTIE_EXPEDITION_TAB_720P.png'
CAMPAIGN_TAB_TEMPLATE = 'SORTIE_CAMPAIGN_TAB_720P.png'
DECISIVE_TAB_TEMPLATE = 'SORTIE_DECISIVE_TAB_720P.png'


# ── 标签栏识别区域 ──────────────────────────────────────────────────────────

# 校准基准 1280x720；区域由 SORTIE_TAB_ROI_REPORT.json 的像素框换算为四位小数，
# 并按 [规范]python-code-style.md §6.5 外扩，保证区域大于对应模板。
SORTIE_TAB_ROI = ROI(0.1539, 0.0166, 0.2149, 0.0723)
EXERCISE_TAB_ROI = ROI(0.2796, 0.0152, 0.3438, 0.075)
EXPEDITION_TAB_ROI = ROI(0.4078, 0.0138, 0.4735, 0.0764)
CAMPAIGN_TAB_ROI = ROI(0.5367, 0.0138, 0.6008, 0.0764)
DECISIVE_TAB_ROI = ROI(0.6656, 0.0166, 0.7336, 0.075)


# 切到这个标签后页面要走一段切换动画；执行器点完标签只确认一次，
# 因此默认给足重试（7 次 x 0.5 秒，约 3.5 秒），动画没走完时继续等。
_TAB_SWITCH_ATTEMPTS = 7
_TAB_SWITCH_INTERVAL_SECONDS = 0.5


# 标签名 → (激活态模板, 识别区域)。供标签中心读取使用。
_TAB_TEMPLATES = {
    'sortie': (SORTIE_TAB_TEMPLATE, SORTIE_TAB_ROI),
    'exercise': (EXERCISE_TAB_TEMPLATE, EXERCISE_TAB_ROI),
    'expedition': (EXPEDITION_TAB_TEMPLATE, EXPEDITION_TAB_ROI),
    'campaign': (CAMPAIGN_TAB_TEMPLATE, CAMPAIGN_TAB_ROI),
    'decisive': (DECISIVE_TAB_TEMPLATE, DECISIVE_TAB_ROI),
}


def check_sortie_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = _TAB_SWITCH_ATTEMPTS,
    interval_seconds: float = _TAB_SWITCH_INTERVAL_SECONDS,
) -> bool:
    """确认出征标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望该标签不再激活时为真，默认期望它激活。
        attempts: 识别次数，默认按标签切换节奏。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真；第一次进入出征页默认落在该标签。
    """
    return expect_template(
        ctx,
        template=_load_template(SORTIE_TAB_TEMPLATE),
        roi=SORTIE_TAB_ROI,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    ).satisfied


def check_exercise_page(ctx: ContextHandle) -> bool:
    """确认演习标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        演习标签激活时为真。
    """
    return expect_template(
        ctx, template=_load_template(EXERCISE_TAB_TEMPLATE), roi=EXERCISE_TAB_ROI
    ).satisfied


def check_expedition_page(ctx: ContextHandle) -> bool:
    """确认远征标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        远征标签激活时为真。
    """
    return expect_template(
        ctx, template=_load_template(EXPEDITION_TAB_TEMPLATE), roi=EXPEDITION_TAB_ROI
    ).satisfied


def check_campaign_page(ctx: ContextHandle) -> bool:
    """确认战役标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        战役标签激活时为真。
    """
    return expect_template(
        ctx, template=_load_template(CAMPAIGN_TAB_TEMPLATE), roi=CAMPAIGN_TAB_ROI
    ).satisfied


def check_decisive_page(ctx: ContextHandle) -> bool:
    """确认决战标签是否激活。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        决战标签激活时为真。
    """
    return expect_template(
        ctx, template=_load_template(DECISIVE_TAB_TEMPLATE), roi=DECISIVE_TAB_ROI
    ).satisfied


def read_tab_center(ctx: ContextHandle, tab: str) -> tuple[float, float]:
    """读取出征页某个标签的中心。

    用激活态模板定位；标签没被选中时模板匹配不上，退回该标签识别区域的中心——
    区域本来就是按校准基准框着这个标签的，中心即落点。因此本函数总能给出坐标，
    调用方不必处理"读不到"。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        tab: 标签名，取值 sortie / exercise / expedition / campaign / decisive。

    Returns:
        标签的归一化中心。

    Raises:
        ValueError: 标签名不在本页标签表内。
    """
    entry = _TAB_TEMPLATES.get(tab)
    if entry is None:
        raise ValueError(f'未知的出征标签: {tab!r}')
    filename, roi = entry
    center = expect_template_center(ctx, template=_load_template(filename), roi=roi, attempts=1)
    if center is None:
        center = ((roi.x1 + roi.x2) / 2, (roi.y1 + roi.y2) / 2)
    return center


# ── 私有辅助 ────────────────────────────────────────────────────────────────


def _load_template(filename: str) -> Template:
    """加载本模块模板。"""
    return load_ui_template(TEMPLATE_NAMESPACE, filename)


__all__ = [
    'check_campaign_page',
    'check_decisive_page',
    'check_exercise_page',
    'check_expedition_page',
    'check_sortie_page',
    'read_tab_center',
]
