"""模块功能：负责后院页面检查、子页面导航和页面回退。

上层调用：
- application.ui.navigation.graph.logistics：调用后院到浴室或食堂的页面边动作。
- application.ui.controller.main_page：查询后院页面匹配结果。
- testing.ui：执行后院页面导航验证。

下层依赖：
- application.ui.controller.backyard_page.constants：提供后院页面专用坐标。
- common.ui.interaction：执行点击后的页面到达等待。
- common.vision：匹配后院页面模板。
- common.types：提供页面名称。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.backyard_page import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page
from autowsgr.common.vision import ImageChecker, PageMatch
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('ui')

# ── 页面目标 ─────────────────────────────────────────────────────────────────


class BackyardTarget(enum.Enum):
    """后院页面可导航的目标。"""

    BATH = '浴室'
    CANTEEN = '食堂'


_NAV_COORDINATES: dict[BackyardTarget, tuple[float, float]] = {
    BackyardTarget.BATH: constants.NAV_POSITIONS['bath'],
    BackyardTarget.CANTEEN: constants.NAV_POSITIONS['canteen'],
}


class BackyardPage:
    """后院页面内的 UI 操作控制器。"""

    def __init__(self, ctx: GameContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面检查 ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """检查截图是否属于后院页面。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            后院页面匹配结果。
        """
        result = ImageChecker.find_template(screen, Templates.Page.BACKYARD, confidence=0.85)
        name = PageName.BACKYARD.value
        if result is None:
            return PageMatch(name=name, matched=False, score=0.0)
        return PageMatch(name=name, matched=True, score=result.confidence)

    # ── 导航 ──────────────────────────────────────────────────────────────

    def navigate_to(self, target: BackyardTarget) -> None:
        """点击导航按钮，进入指定子页面。

        Args:
            target: 导航目标。

        Raises:
            NavigationError: 超时未到达目标页面。
        """
        from autowsgr.application.ui.controller.bath_page import BathPage
        from autowsgr.application.ui.controller.canteen_page import CanteenPage

        target_checker = {
            BackyardTarget.BATH: BathPage.check_current_page,
            BackyardTarget.CANTEEN: CanteenPage.check_current_page,
        }
        _log.info('[UI] 后院 → {}', target.value)
        click_and_wait_for_page(
            self._ctrl,
            click_coord=_NAV_COORDINATES[target],
            checker=target_checker[target],
            source='后院',
            target=target.value,
        )

    def go_to_bath(self) -> None:
        """进入浴室页面。

        Args:
            None.

        Returns:
            None.
        """
        self.navigate_to(BackyardTarget.BATH)

    def go_to_canteen(self) -> None:
        """进入食堂页面。

        Args:
            None.

        Returns:
            None.
        """
        self.navigate_to(BackyardTarget.CANTEEN)

    # ── 回退 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击返回按钮，离开后院并回到主页面。

        Args:
            None.

        Raises:
            NavigationError: 超时仍未离开后院页面。
        """
        from autowsgr.application.ui.controller.main_page import MainPage

        _log.info('[UI] 后院 → 返回主页面')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=MainPage.is_current_page,
            source='后院',
            target=PageName.MAIN,
        )
