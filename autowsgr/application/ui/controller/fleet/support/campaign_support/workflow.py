"""模块功能：编排战役支援目标状态确认、切换和复查。

上层调用：
- main_page.page、application.combat：请求战役支援处于目标状态。

下层依赖：
- campaign_support.recognition：读取当前支援状态。
- campaign_support.constants：提供按钮坐标和同步参数。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.fleet.support.campaign_support import (
    constants,
    recognition,
)
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from autowsgr.application.ui.context import UIContext


_log = get_logger('ui.fleet.support.campaign_support')


def apply_campaign_support(ctx: UIContext, *, enabled: bool = True) -> None:
    """确保战役支援处于目标状态，并在切换后复查。"""
    status = recognition.read_support_status(ctx.ctrl.screenshot())
    if status is recognition.SupportStatus.EXHAUSTED:
        if enabled:
            return
        raise RuntimeError('战役支援次数已耗尽，无法关闭支援')
    if (status is recognition.SupportStatus.ENABLED) == enabled:
        return
    switch_campaign_support(ctx)
    time.sleep(constants.SUPPORT_SWITCH_WAIT)
    actual = recognition.read_support_status(ctx.ctrl.screenshot())
    if actual is recognition.SupportStatus.EXHAUSTED:
        raise RuntimeError('战役支援切换后变为耗尽状态')
    actual_enabled = actual is recognition.SupportStatus.ENABLED
    if actual_enabled != enabled:
        raise RuntimeError(f'战役支援状态切换失败: 目标={enabled} 实际={actual.value}')


def switch_campaign_support(ctx: UIContext) -> None:
    """点击战役支援开关。"""
    _log.debug('[UI] 出征准备 -> 切换战役支援')
    ctx.ctrl.click(*constants.CLICK_SUPPORT)


__all__ = ['apply_campaign_support', 'switch_campaign_support']
