"""模块功能：从截图识别侧边栏页面事实。

上层调用：
- application.ui.controller.sidebar.main_page.page：提供侧边栏页面检查契约。

下层依赖：
- common.vision：提供模板匹配能力。
- common.vision.resources：提供侧边栏页面模板。
- common.types：提供页面名称。

边界：
本模块只转换截图为侧边栏页面匹配结果，不执行设备操作、页面导航或运行时状态管理。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.types import PageName
from autowsgr.common.vision import ImageChecker, PageMatch
from autowsgr.application.vision.resources import Templates


if TYPE_CHECKING:
    import numpy


def recognize_sidebar_page(screen: numpy.ndarray) -> PageMatch:
    """从截图识别侧边栏页面。

    Args:
        screen: RGB 截图，形状为 ``(H, W, 3)``。

    Returns:
        侧边栏页面匹配结果。
    """
    result = ImageChecker.find_template(screen, Templates.Page.SIDEBAR, confidence=0.8)
    name = PageName.SIDEBAR.value
    if result is None:
        return PageMatch(name=name, matched=False, score=0.0)
    return PageMatch(name=name, matched=True, score=result.confidence)


__all__ = ['recognize_sidebar_page']
