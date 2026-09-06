"""后院页面 UI 控制器。

已完成

使用方式::

    from autowsgr.application.ui.controller.backyard_page import BackyardPage, BackyardTarget

    page = BackyardPage(ctrl)
    page.go_to_bath()
    page.go_back()
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.common.calibration.backyard import CLICK_BACK, NAV_POSITIONS
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page
from autowsgr.common.vision import ImageChecker, PageMatch
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('ui')

# ═══════════════════════════════════════════════════════════════════════════════
# 枚举
# ═══════════════════════════════════════════════════════════════════════════════


class BackyardTarget(enum.Enum):
    """后院页面可导航的目标。"""

    BATH = '浴室'
    CANTEEN = '食堂'


# ═══════════════════════════════════════════════════════════════════════════════
# 页面识别签名
# ═══════════════════════════════════════════════════════════════════════════════



# ═══════════════════════════════════════════════════════════════════════════════
# 点击坐标
# ═══════════════════════════════════════════════════════════════════════════════




# ═══════════════════════════════════════════════════════════════════════════════
# 页面控制器
# ═══════════════════════════════════════════════════════════════════════════════


CLICK_NAV: dict[BackyardTarget, tuple[float, float]] = {
    BackyardTarget.BATH: NAV_POSITIONS['bath'],
    BackyardTarget.CANTEEN: NAV_POSITIONS['canteen'],
}


class BackyardPage:
    """后院页面控制器。

    Parameters
    ----------
    ctrl:
        Android 设备控制器实例。
    """

    def __init__(self, ctx: GameContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面识别 ──────────────────────────────────────────────────────────

    @staticmethod
    def is_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否为后院页面。

        用后院页面独有特征模板匹配 (迁移自 classic ``backyard_page``,
        482x387 大区域模板, 区分度极高), 返回带置信度的
        :class:`PageMatch` 供候选集排序。旧像素签名 ``PAGE_SIGNATURE``
        保留备查, 不再参与判定。

        Parameters
        ----------
        screen:
            截图 (HxWx3, RGB)。
        """
        result = ImageChecker.find_template(screen, Templates.Page.BACKYARD, confidence=0.85)
        name = PageName.BACKYARD.value
        if result is None:
            return PageMatch(name=name, matched=False, score=0.0)
        return PageMatch(name=name, matched=True, score=result.confidence)

    # ── 导航 ──────────────────────────────────────────────────────────────

    def navigate_to(self, target: BackyardTarget) -> None:
        """点击导航按钮，进入指定子页面。

        Parameters
        ----------
        target:
            导航目标。

        Raises
        ------
        NavigationError
            超时未到达目标页面。
        """
        from .bath_page import BathPage
        from .canteen_page import CanteenPage

        target_checker = {
            BackyardTarget.BATH: BathPage.is_current_page,
            BackyardTarget.CANTEEN: CanteenPage.is_current_page,
        }
        _log.info('[UI] 后院 → {}', target.value)
        click_and_wait_for_page(
            self._ctrl,
            click_coord=CLICK_NAV[target],
            checker=target_checker[target],
            source='后院',
            target=target.value,
        )

    def go_to_bath(self) -> None:
        """进入浴室 (修理舰船)。"""
        self.navigate_to(BackyardTarget.BATH)

    def go_to_canteen(self) -> None:
        """进入食堂。"""
        self.navigate_to(BackyardTarget.CANTEEN)

    # ── 回退 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击回退按钮 (◁)，返回主页面。

        Raises
        ------
        NavigationError
            超时仍在后院页面。
        """
        from .main_page import MainPage

        _log.info('[UI] 后院 → 返回主页面')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=CLICK_BACK,
            checker=MainPage.is_current_page,
            source='后院',
            target=PageName.MAIN,
        )
