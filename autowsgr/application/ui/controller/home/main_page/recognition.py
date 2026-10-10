"""模块功能：识别主页通知事实。

上层调用：
- application.ui.controller.home.main_page.page：读取主页通知状态。
- business.logistics：判断远征与任务是否完成。

下层依赖：
- main_page.constants：提供通知的像素规则。
- common.vision：提供像素识别入口。

边界：只读取通知事实，不执行点击、不导航、不编排流程。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home.main_page import constants
from autowsgr.common.vision import expect_pixels


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


def check_expedition_ready(ctx: ContextHandle) -> bool:
    """检查远征完成通知是否出现。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        远征通知探针命中时为真。
    """
    result = expect_pixels(ctx, signature=constants.EXPEDITION_READY_SIGNATURE, attempts=1)
    return result.satisfied


def check_task_ready(ctx: ContextHandle) -> bool:
    """检查任务奖励通知是否出现。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        任务通知探针命中时为真。
    """
    result = expect_pixels(ctx, signature=constants.TASK_READY_SIGNATURE, attempts=1)
    return result.satisfied


__all__ = ['check_expedition_ready', 'check_task_ready']
