"""模块功能：识别登录前启动画面并点击进入游戏。

上层调用：
- application.runtime.startup：等待游戏 UI 就绪并处理冷启动入口。
- application.runtime.initialize.initialize：执行非运行状态下的登录进入步骤。

下层依赖：
- application.ui.controller.login.constants：提供启动画面坐标和像素签名。
- common.system.logger：记录启动画面操作。
- common.vision：执行像素签名检查并返回统一页面匹配结果。

启动画面没有游戏内父页面，因此不提供业务意义上的 ``go_back``。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.login import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import PageMatch, PixelChecker


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.device import AndroidController


_log = get_logger('ui')

_CLICK_SETTLE = 2.0
"""点击进入后等待画面稳定的时间 (秒)。"""


class LoginPage:
    """游戏登录前启动画面的 UI 控制器。

    Parameters
    ----------
    ctrl:
        Android 设备控制器实例。
    """

    def __init__(self, ctrl: AndroidController) -> None:
        self._ctrl = ctrl

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否为登录前启动画面。

        Parameters
        ----------
        screen:
            截图 (HxWx3, RGB)。

        Returns
        -------
        PageMatch
            启动画面的像素签名匹配结果。
        """
        result = PixelChecker.check_signature(screen, constants.PAGE_SIGNATURE)
        return PageMatch(
            name=constants.PAGE_SIGNATURE.name,
            matched=result.matched,
            score=result.ratio,
        )

    def click_enter(self) -> None:
        """点击启动画面的进入按钮，继续游戏登录流程。"""
        _log.info('[UI] 点击「点击进入」按钮 {}', constants.CLICK_ENTER)
        self._ctrl.click(*constants.CLICK_ENTER)
        time.sleep(_CLICK_SETTLE)
