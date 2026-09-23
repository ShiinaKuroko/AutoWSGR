"""模块功能：根据单帧截图确认当前是否为主页。

上层调用：
- application.ui.navigation.page_checker.registry：提供主页识别事实。

下层依赖：
- common.vision：加载主页模板并执行 ROI 匹配。
- common.vision.operations.template_matching：提供模板和 ROI 契约。

本模块只读取传入截图并返回一次识别结果，不截图、不重试、不处理主页浮层。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common import vision
from autowsgr.common.vision.operations.template_matching import ROI, Template


if TYPE_CHECKING:
    import numpy as np


_HOME_PAGE_ROI = ROI(0.9109, 0.8681, 0.9758, 0.9139)
_HOME_PAGE_CONFIDENCE = 0.85
_HOME_TEMPLATE_PATH = 'application/ui/navigation/page_checker/HOME/HOME_MAIN_720P.png'


def check_home_page(screen: np.ndarray) -> bool:
    """判断一帧截图是否命中主页模板。"""
    template = Template(
        name='home_main',
        relative_path=_HOME_TEMPLATE_PATH,
        image=vision.opencv.load_image(_HOME_TEMPLATE_PATH),
        source_resolution=(1280, 720),
    )
    return vision.match_template(
        screen,
        template,
        roi=_HOME_PAGE_ROI,
        confidence=_HOME_PAGE_CONFIDENCE,
    ).matched


__all__ = ['check_home_page']
