"""负责后院页面检查、子页面导航和页面回退。

上层调用：
- application.ui.navigation.graph.logistics：执行后院页面边动作。
- application.ui.controller.home.main_page：取得后院页面检查器。
- testing.ui：执行后院页面导航验证。

下层依赖：
- application.ui.controller.backyard.main_page.constants：提供页面导航坐标。
- application.ui.controller.backyard.main_page.recognition：提供后院页面识别结果。
- common.device.interaction：执行点击和页面到达等待。
- common.types：提供页面名称和匹配结果。

边界：
只编排后院页面内动作，不实现视觉识别，不负责跨页面寻路或业务调度。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.backyard.main_page import constants, recognition
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.interaction import click_and_wait_for_page


if TYPE_CHECKING:
    import numpy

    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.application.ui.navigation.types import PageMatch


_log = get_logger('ui.backyard.main_page')


# ── 页面目标 ──────────────────────────────────────────────────────────────────────


class BackyardTarget(enum.Enum):
    """后院页面可导航的目标。"""

    BATH = '浴室'
    CANTEEN = '食堂'


_NAV_COORDINATES: dict[BackyardTarget, tuple[float, float]] = {
    BackyardTarget.BATH: constants.CLICK_BATH,
    BackyardTarget.CANTEEN: constants.CLICK_CANTEEN,
}


class BackyardPage:
    """后院页面内的 UI 操作控制器。"""

    def __init__(self, ctx: UIContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面检查 ──────────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: numpy.ndarray) -> PageMatch:
        """检查截图是否属于后院页面。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            后院页面匹配结果。
        """
        return recognition.check_current_page(screen)

    # ── 页面导航 ──────────────────────────────────────────────────────────────────

    def navigate_to(self, target: BackyardTarget) -> None:
        """点击导航按钮，进入指定子页面。

        Args:
            target: 导航目标。

        Raises:
            NavigationError: 超时未到达目标页面。
        """
        # 页面子控制器会回退到当前后院页面，局部导入用于避免页面包初始化循环。
        from autowsgr.application.ui.controller.backyard.bath_page import BathPage
        from autowsgr.application.ui.controller.backyard.canteen_page import CanteenPage

        # 1. 确定目标子页面的终态检查器，避免点击后无法确认导航结果。
        target_checker = {
            BackyardTarget.BATH: BathPage.check_current_page,
            BackyardTarget.CANTEEN: CanteenPage.check_current_page,
        }

        # 2. 点击后院入口并确认目标子页面已经到达。
        click_and_wait_for_page(
            self._ctrl,
            click_coord=_NAV_COORDINATES[target],
            checker=target_checker[target],
            source='后院',
            target=target.value,
        )
        _log.info('[UI] 后院 → 进入：目标={!r}，结果=成功', target.value)

    def go_to_bath(self) -> None:
        """进入浴室页面。"""
        self.navigate_to(BackyardTarget.BATH)

    def go_to_canteen(self) -> None:
        """进入食堂页面。"""
        self.navigate_to(BackyardTarget.CANTEEN)

    # ── 页面回退 ──────────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击返回按钮，离开后院并回到主页面。

        Raises:
            NavigationError: 超时仍未离开后院页面。
        """
        # 主页控制器也提供后院检查器，局部导入用于保持页面包的延迟互相引用。
        from autowsgr.application.ui.controller.home.main_page import HomePage

        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=HomePage.check_current_page,
            source='后院',
            target=PageName.HOME.value,
        )
        _log.info('[UI] 后院 → 返回：目标={!r}，结果=成功', PageName.HOME.value)
