"""模块功能：读取出征页当前激活的标签页。

上层调用：
- application.ui.navigation.registry：作为出征页域的探针，一帧判出当前停在哪个标签页。
- application.ui.navigation.executor：切换标签后确认落点。

下层依赖：
- application.ui.template：加载本模块的激活态模板。
- common.vision：按模板与区域识别当前激活的标签。

边界：只做识别并返回页面结论，不执行点击、不计算路由、不上报识别错误。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.template import load_ui_template
from autowsgr.common.vision import ROI, Template, expect_template


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


# ── 识别数据 ────────────────────────────────────────────────────────────────

# 本模块在 UI 模板根下的命名空间。
TEMPLATE_NAMESPACE = 'navigation/checker/sortie'

# 五个标签的激活态模板；目录小写、文件名全大写。
# 只保留激活态：标签互斥，一次只有一个激活模板能匹配上。
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

# 页面、激活态模板与识别区域；五个区域互不重叠，顺序即判定顺序。
_TAB_LAYERS: tuple[tuple[PageName, str, ROI], ...] = (
    (PageName.SORTIE_MAP, SORTIE_TAB_TEMPLATE, SORTIE_TAB_ROI),
    (PageName.EXERCISE, EXERCISE_TAB_TEMPLATE, EXERCISE_TAB_ROI),
    (PageName.EXPEDITION, EXPEDITION_TAB_TEMPLATE, EXPEDITION_TAB_ROI),
    (PageName.CAMPAIGN, CAMPAIGN_TAB_TEMPLATE, CAMPAIGN_TAB_ROI),
    (PageName.DECISIVE_BATTLE, DECISIVE_TAB_TEMPLATE, DECISIVE_TAB_ROI),
)

# 切标签后页面要走一段切换动画；读一帧判层时不需要等，默认只读一次。
_READ_ATTEMPTS = 1
_READ_INTERVAL_SECONDS = 0.5


# ── 当前标签页 ──────────────────────────────────────────────────────────────


def read_sortie_tab_layer(
    ctx: ContextHandle,
    *,
    attempts: int = _READ_ATTEMPTS,
    interval_seconds: float = _READ_INTERVAL_SECONDS,
) -> PageName | None:
    """读取出征页当前激活的标签页。

    五个标签互斥，一次截图按各自区域匹配五个激活态模板，命中的那个就是当前页。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        attempts: 识别次数；判层默认只读一帧，切标签确认时由调用方提高。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        当前激活标签对应的页面；不在任何标签页时为 None。
    """
    result = expect_template(
        ctx,
        template=tuple(_load_template(filename) for _, filename, _ in _TAB_LAYERS),
        roi=tuple(roi for _, _, roi in _TAB_LAYERS),
        attempts=attempts,
        interval_seconds=interval_seconds,
    )
    for (page, _, _), match in zip(_TAB_LAYERS, result.observation, strict=True):
        if match.matched:
            return page
    return None


# ── 私有辅助 ────────────────────────────────────────────────────────────────


def _load_template(filename: str) -> Template:
    """加载本模块模板。"""
    return load_ui_template(TEMPLATE_NAMESPACE, filename)


__all__ = ['read_sortie_tab_layer']
