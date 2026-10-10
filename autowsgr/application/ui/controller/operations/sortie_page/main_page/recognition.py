"""模块功能：读取出征页顶部的远征通知事实。

上层调用：
- business.logistics.expedition：判断远征是否完成。

下层依赖：
- main_page.constants：提供远征通知的像素规则。
- common.vision：提供像素识别入口。

边界：只读取通知事实，不执行设备操作、不导航、不点击。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.main_page import constants
from autowsgr.common.vision import expect_pixels


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


def check_expedition_notification(ctx: ContextHandle) -> bool:
    """判断出征页顶部是否显示远征完成通知。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        通知探针命中时为真。
    """
    result = expect_pixels(ctx, signature=constants.EXPEDITION_NOTIF_SIGNATURE, attempts=1)
    return result.satisfied
