"""模块功能：截图并识别当前是否位于出征页面。

上层调用：application.ui.navigation：调用出征页页面识别。

下层依赖：
- application.ui.recognition_flow：截图、记录 Context 并重试识别。
- common.vision.adapters.template_matching：加载出征页模板并匹配区域。

边界：返回模板识别事实，不写入 Navigator 确认状态或执行页面动作。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui import recognition_flow
from autowsgr.common import vision
from autowsgr.common.vision.adapters.template_matching import ROI, Template


if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np

    from autowsgr.common.device.service import DeviceService


_SORTIE_TEMPLATE_ROOT = 'application/ui/navigation/page_checker/SORTIE'
_SORTIE_TAB_CONFIDENCE = 0.85
_SORTIE_REQUIRED_MATCHES = 3
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


def check_sortie_page(
    ctrl: DeviceService,
    *,
    record_screenshot: Callable[[np.ndarray], None],
) -> bool:
    """截图并使用出征页模板识别当前页面。

    Args:
        ctrl: 提供截图能力的设备服务。
        record_screenshot: 将每次截图保存到当前任务 Context 的回调。

    Returns:
        命中出征页模板时返回 True。
    """
    templates = tuple(
        Template(
            name=relative_path.rsplit('/', 1)[-1].removesuffix('.png'),
            relative_path=relative_path,
            image=vision.opencv.load_image(relative_path),
            source_resolution=(1280, 720),
        )
        for relative_path in _SORTIE_TEMPLATE_PATHS
    )
    result = recognition_flow.recognize_with_retry(
        ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=templates,
        roi=_SORTIE_TAB_ROIS,
        confidence=_SORTIE_TAB_CONFIDENCE,
        record_screenshot=record_screenshot,
        is_match=lambda matches: (
            sum(match.matched for match in matches) >= _SORTIE_REQUIRED_MATCHES
        ),
    )
    return result.satisfied


__all__ = ['check_sortie_page']
