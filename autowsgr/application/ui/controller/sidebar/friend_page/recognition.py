"""识别好友页面事实。

上层调用：
- application.ui.controller.sidebar.friend_page.page：提供好友页面检查结果。

下层依赖：
- application.ui.controller.operations.sortie_page.main_page：提供通用标签页识别能力。

边界：
只读取截图并返回好友页面匹配结果，不执行设备操作、页面导航或业务调度。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    TabbedPageType,
    check_tabbed_page,
)


if TYPE_CHECKING:
    import numpy

    from autowsgr.application.ui.navigation.types import PageMatch


def check_current_page(screen: numpy.ndarray) -> PageMatch:
    """检查截图是否属于好友页面。

    Args:
        screen: 好友页面 RGB 截图，形状为 ``(H, W, 3)``。

    Returns:
        好友页面匹配结果。
    """
    return check_tabbed_page(screen, TabbedPageType.FRIEND)


__all__ = ['check_current_page']
