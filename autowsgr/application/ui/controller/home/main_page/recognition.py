"""模块功能：识别主页通知事实。

上层调用：
- application.ui.controller.home.main_page.page：读取主页通知状态。

下层依赖：
- common.vision：提供像素采样能力。
- main_page.constants：提供通知探针位置、颜色和容差。

边界：只读取主页通知事实，不识别浮窗、不执行点击。

浮窗识别已迁移到导航器的 `page_checker.home_checker`；本模块当前引用的 `vision.numpy`
入口在 `common.vision` 重写后已不存在，通知识别待后续批按新入口重写。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home.main_page import constants
from autowsgr.common import vision


if TYPE_CHECKING:
    import numpy as np


def check_expedition_ready(screen: np.ndarray) -> bool:
    """检查远征完成通知颜色是否出现。"""
    return _check_notification(screen, 'expedition_ready')


def check_task_ready(screen: np.ndarray) -> bool:
    """检查任务奖励通知颜色是否出现。"""
    return _check_notification(screen, 'task_ready')


def _check_notification(screen: np.ndarray, name: str) -> bool:
    """检查一个命名主页通知探针。"""
    pixel = vision.numpy.sample_pixel(screen, *constants.PROBE_POSITIONS[name])
    return constants.NOTIFICATION_RED.near(
        type(constants.NOTIFICATION_RED)(*pixel),
        constants.NOTIFICATION_RED_TOLERANCE,
    )


__all__ = ['check_expedition_ready', 'check_task_ready']
