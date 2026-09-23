"""识别后院页面事实。

上层调用：
- application.ui.controller.backyard.main_page.page：提供后院页面检查结果。

下层依赖：
- common.vision：匹配后院页面模板并构造页面匹配结果。
- common.types：提供页面名称。

边界：
只读取截图并返回后院页面匹配结果，不执行设备操作、页面导航或业务调度。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common import vision
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.vision.resources import Templates


if TYPE_CHECKING:
    import numpy


_BACKYARD_PAGE_CONFIDENCE: float = 0.85
"""后院页面模板的最低识别置信度。"""


def check_current_page(screen: numpy.ndarray) -> vision.PageMatch:
    """检查截图是否属于后院页面。

    Args:
        screen: 后院页面 RGB 截图，形状为 ``(H, W, 3)``。

    Returns:
        后院页面匹配结果。
    """
    result = vision.ImageChecker.find_template(
        screen,
        Templates.Page.BACKYARD,
        confidence=_BACKYARD_PAGE_CONFIDENCE,
    )
    name = PageName.BACKYARD.value
    if result is None:
        return vision.PageMatch(name=name, matched=False, score=0.0)
    return vision.PageMatch(name=name, matched=True, score=result.confidence)


__all__ = ['check_current_page']
