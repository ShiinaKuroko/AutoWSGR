"""游戏「点击进入」启动画面 UI 控制器。

游戏冷启动后、进入主流程前会停在此画面，需要点击右下角按钮才能继续。
(从 ui/start_screen_page.py 迁入, 老路径已留兼容 shim)

使用方式::

    from autowsgr.infra.base.ui.pages.start_screen import StartScreenPage

    screen = ctrl.screenshot()
    if StartScreenPage.is_current_page(screen):
        StartScreenPage(ctrl).click_enter()
        # 之后开始检测登录浮层
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.infra.base.constants.coordinates import point
from autowsgr.infra.base.constants.signatures import signature
from autowsgr.infra.logger import get_logger
from autowsgr.vision import (
    PageMatch,
    PixelChecker,
)


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.emulator import AndroidController


_log = get_logger('ui')

# ═══════════════════════════════════════════════════════════════════════════════
# 页面识别签名
# ═══════════════════════════════════════════════════════════════════════════════

#: 启动画面像素签名 — 底部横幅暖黄色调特征 (数据源: signatures/start_screen.yaml)
PAGE_SIGNATURE = signature('start_screen', 'page')


# ═══════════════════════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════════════════════

#: 「点击进入」按钮坐标（右下角）— 数据源: coordinates/login.yaml
CLICK_ENTER: tuple[float, float] = point('login', 'enter_game')

#: 点击后等待画面稳定的时间（秒）
_CLICK_SETTLE: float = 2.0


# ═══════════════════════════════════════════════════════════════════════════════
# 页面控制器
# ═══════════════════════════════════════════════════════════════════════════════


class StartScreenPage:
    """游戏「点击进入」启动画面控制器。

    **状态查询** 为 ``staticmethod``，只需截图即可调用。
    **操作动作** 为实例方法，通过注入的控制器执行。

    Parameters
    ----------
    ctrl:
        Android 设备控制器实例。
    """

    def __init__(self, ctrl: AndroidController) -> None:
        self._ctrl = ctrl

    # ── 页面识别 ──────────────────────────────────────────────────────────

    @staticmethod
    def is_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否为启动画面。

        通过底部横幅暖黄色调像素签名匹配判定。
        返回带匹配比例的 :class:`PageMatch`
        (``PageMatch.__bool__`` 保证旧式真值调用不变)。

        Parameters
        ----------
        screen:
            截图 (HxWx3, RGB)。
        """
        result = PixelChecker.check_signature(screen, PAGE_SIGNATURE)
        return PageMatch(
            name=PAGE_SIGNATURE.name,
            matched=result.matched,
            score=result.ratio,
        )

    # ── 操作动作 ──────────────────────────────────────────────────────────

    def click_enter(self) -> None:
        """点击右下角「点击进入」按钮，进入游戏主流程。

        点击坐标为 :data:`CLICK_ENTER` (读自 login.yaml)，点击后等待
        :data:`_CLICK_SETTLE` 秒让画面稳定，之后可开始检测登录浮层。
        """
        _log.info('[UI] 点击「点击进入」按钮 {}', CLICK_ENTER)
        self._ctrl.click(*CLICK_ENTER)
        time.sleep(_CLICK_SETTLE)
