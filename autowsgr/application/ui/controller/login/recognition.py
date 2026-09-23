"""识别登录前启动画面事实。

上层调用：
- application.ui.controller.login.page：提供启动画面检查结果。

下层依赖：
- application.ui.controller.login.constants：提供启动画面像素签名。
- common.vision：执行像素签名检查并构造页面匹配结果。

边界：
只读取截图并返回启动画面匹配结果，不执行设备操作、游戏启动或页面导航。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.login import constants
from autowsgr.common import vision


if TYPE_CHECKING:
    import numpy


def check_current_page(screen: numpy.ndarray) -> vision.PageMatch:
    """判断截图是否为登录前启动画面。

    Args:
        screen: 登录启动画面 RGB 截图，形状为 ``(H, W, 3)``。

    Returns:
        启动画面的像素签名匹配结果。
    """
    result = vision.PixelChecker.check_signature(screen, constants.PAGE_SIGNATURE)
    return vision.PageMatch(
        name=constants.PAGE_SIGNATURE.name,
        matched=result.matched,
        score=result.ratio,
    )


__all__ = ['check_current_page']
