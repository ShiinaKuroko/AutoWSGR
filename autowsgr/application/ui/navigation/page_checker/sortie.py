"""模块功能：根据单帧截图确认当前是否为出征页面主面板。

上层调用：
- application.ui.navigation.page_checker.registry：提供出征页识别事实。

下层依赖：
- common.vision：加载 tab 模板并执行 ROI 匹配。
- common.vision.operations.template_matching：提供模板和 ROI 契约。

本模块只确认出征页顶部 tab 状态，不截图、不重试、不执行页面动作或业务流程。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common import vision
from autowsgr.common.vision.operations.template_matching import ROI, Template


if TYPE_CHECKING:
    import numpy as np


_SORTIE_TEMPLATE_ROOT = 'application/ui/navigation/page_checker/SORTIE'
_SORTIE_TAB_CONFIDENCE = 0.85
_SORTIE_TEMPLATE_PATHS = (
    f'{_SORTIE_TEMPLATE_ROOT}/SORTIE_SORTIE_TAB_720P.png',
    f'{_SORTIE_TEMPLATE_ROOT}/SORTIE_EXERCISE_TAB_INACTIVE_720P.png',
    f'{_SORTIE_TEMPLATE_ROOT}/SORTIE_EXPEDITION_TAB_INACTIVE_720P.png',
    f'{_SORTIE_TEMPLATE_ROOT}/SORTIE_CAMPAIGN_TAB_INACTIVE_720P.png',
    f'{_SORTIE_TEMPLATE_ROOT}/SORTIE_DECISIVE_TAB_INACTIVE_720P.png',
)
_SORTIE_TAB_ROIS = (
    ROI(0.1540, 0.0167, 0.2157, 0.0737),
    ROI(0.2797, 0.0153, 0.3446, 0.0764),
    ROI(0.4079, 0.0139, 0.4743, 0.0778),
    ROI(0.5368, 0.0139, 0.6016, 0.0778),
    ROI(0.6657, 0.0167, 0.7344, 0.0764),
)


def check_sortie_page(screen: np.ndarray) -> bool:
    """确认一帧截图位于出征页面主面板。"""
    for relative_path, roi in zip(_SORTIE_TEMPLATE_PATHS, _SORTIE_TAB_ROIS, strict=True):
        template = Template(
            name=relative_path.rsplit('/', 1)[-1].removesuffix('.png'),
            relative_path=relative_path,
            image=vision.opencv.load_image(relative_path),
            source_resolution=(1280, 720),
        )
        if not vision.match_template(
            screen,
            template,
            roi=roi,
            confidence=_SORTIE_TAB_CONFIDENCE,
        ).matched:
            return False
    return True


__all__ = ['check_sortie_page']
