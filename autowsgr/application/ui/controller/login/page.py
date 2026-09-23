"""模块功能：编排登录前启动画面的识别和进入游戏流程。

上层调用：
- application.runtime.startup：等待游戏 UI 就绪并处理冷启动入口。
- application.runtime.initialize.initialize：执行非运行状态下的登录进入步骤。

下层依赖：
- application.ui.controller.login.constants：提供启动画面坐标和像素签名。
- application.ui.controller.login.recognition：提供启动画面识别结果。
- common.system.logger：记录启动画面操作。
- common.device：提供游戏设备控制器。
- common.vision：提供统一页面匹配结果类型。

边界：
只编排启动画面识别和进入游戏，不负责游戏启动、登录后页面导航或浮层处理。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.login import constants, recognition
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    import numpy

    from autowsgr.common.device.service import DeviceService
    from autowsgr.application.ui.navigation.types import PageMatch


_log = get_logger('ui.login')

_ENTER_GAME_SETTLE_SECONDS: float = 2.0
"""点击进入后等待登录启动画面过渡的时间 (秒)。"""


class LoginPage:
    """游戏登录前启动画面的 UI 控制器。"""

    def __init__(self, ctrl: DeviceService) -> None:
        """保存登录启动画面的设备控制器。

        Args:
            ctrl: Android 设备控制器实例。
        """
        self._ctrl = ctrl

    # ── 启动画面识别 ───────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: numpy.ndarray) -> PageMatch:
        """判断截图是否为登录前启动画面。

        Args:
            screen: 登录启动画面 RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            启动画面的像素签名匹配结果。
        """
        return recognition.check_current_page(screen)

    # ── 登录启动流程 ───────────────────────────────────────────────────────────────

    def enter_game(self) -> None:
        """提交进入游戏动作并等待启动画面过渡。

        登录后的页面终态由运行时启动流程继续确认。
        """

        # 1. 提交进入游戏动作，将登录后的页面确认交给运行时流程。
        _log.info('[UI] 登录画面 → 尝试进入')
        self._ctrl.click(*constants.CLICK_ENTER)

        # 2. 等待启动画面过渡，避免运行时在点击动画期间重复读取状态。
        time.sleep(_ENTER_GAME_SETTLE_SECONDS)
        _log.info('[UI] 登录画面 → 进入游戏：结果=已提交')
