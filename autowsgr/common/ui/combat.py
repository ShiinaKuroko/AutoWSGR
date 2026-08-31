"""战斗页面使用的通用模板点击原语。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision.image_matcher import ImageChecker
from autowsgr.common.vision.resources import TemplateKey, Templates


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.device import AndroidController


_log = get_logger('combat')


def click_image(
    device: AndroidController,
    template_key: TemplateKey | str,
    timeout: float,
) -> bool:
    """等待模板出现并点击其中心。"""
    if isinstance(template_key, str):
        template_key = TemplateKey(template_key)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        detail = ImageChecker.find_any(
            device.screenshot(),
            template_key.templates,
            confidence=0.8,
        )
        if detail is not None:
            device.click(*detail.center)
            return True
        time.sleep(0.3)
    return False


def dismiss_resource_confirm(device: AndroidController, screen: np.ndarray) -> None:
    """在当前截图中发现资源确认弹窗时点击确认。"""
    detail = ImageChecker.find_any(
        screen,
        [Templates.Confirm.CONFIRM_1],
        confidence=0.75,
    )
    if detail is None:
        return
    time.sleep(0.25)
    device.click(*detail.center, delay=False)
    _log.info(
        "[Combat] 点掉资源确认弹窗: '{}' ({:.4f}, {:.4f})",
        detail.template_name,
        *detail.center,
    )


__all__ = ['click_image', 'dismiss_resource_confirm']
