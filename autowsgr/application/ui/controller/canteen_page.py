"""食堂页面 UI 控制器。

已完成 需测试

覆盖游戏 **食堂** (料理/食堂) 页面的导航交互。

使用方式::

    from autowsgr.application.ui.controller.canteen_page import CanteenPage

    page = CanteenPage(ctrl)
    page.go_back()
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.common.calibration.canteen import (
    CLICK_BACK,
    CLICK_CANCEL_COOK,
    CLICK_DISMISS_POPUP,
    CLICK_FORCE_COOK,
    CLICK_SKIP_ANIMATION,
    RECIPE_POSITIONS as CLICK_RECIPE,
)
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
# 页面识别签名
# ═══════════════════════════════════════════════════════════════════════════════



# ═══════════════════════════════════════════════════════════════════════════════
# 点击坐标
# ═══════════════════════════════════════════════════════════════════════════════



# ── 做菜弹窗坐标 ──────────────────────────────────────────────────────





# ═══════════════════════════════════════════════════════════════════════════════
# 页面控制器
# ═══════════════════════════════════════════════════════════════════════════════


class CanteenPage:
    """食堂页面控制器。

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
        """判断截图是否为食堂页面。

        用食堂页面独有特征模板匹配 (迁移自 classic ``canteen_page``, 86x33
        局部特征), 返回带置信度的 :class:`PageMatch` 供候选集排序。
        旧像素签名 ``PAGE_SIGNATURE`` 保留备查, 不再参与判定。

        Parameters
        ----------
        screen:
            截图 (HxWx3, RGB)。
        """
        result = ImageChecker.find_template(screen, Templates.Page.CANTEEN, confidence=0.85)
        name = PageName.CANTEEN.value
        if result is None:
            return PageMatch(name=name, matched=False, score=0.0)
        return PageMatch(name=name, matched=True, score=result.confidence)

    # ── 回退 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击回退按钮 (◁)，返回后院。

        Raises
        ------
        NavigationError
            超时仍在食堂页面。
        """
        from autowsgr.application.ui.controller.backyard_page import BackyardPage

        _log.info('[UI] 食堂 → 返回后院')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=CLICK_BACK,
            checker=BackyardPage.is_current_page,
            source='食堂',
            target='后院',
        )

    # ── 操作 ──────────────────────────────────────────────────────────────

    def select_recipe(self, position: int) -> None:
        """点击选择菜谱。

        Parameters
        ----------
        position:
            菜谱编号 (1-3)。

        Raises
        ------
        ValueError
            编号不在 1-3 范围内。
        """
        if position not in CLICK_RECIPE:
            raise ValueError(f'菜谱编号必须为 1-3，收到: {position}')
        _log.info('[UI] 食堂 → 选择菜谱 {}', position)
        self._ctrl.click(*CLICK_RECIPE[position])

    def confirm_force_cook(self) -> None:
        """「效果正在生效」弹窗 → 点击继续做菜。"""
        _log.info('[UI] 食堂 → 确认继续做菜 (覆盖生效中的菜)')
        self._ctrl.click(*CLICK_FORCE_COOK)

    def cancel_force_cook(self) -> None:
        """「效果正在生效」弹窗 → 取消做菜。"""
        _log.info('[UI] 食堂 → 取消做菜 (保留生效中的菜)')
        self._ctrl.click(*CLICK_CANCEL_COOK)

    def dismiss_popup(self) -> None:
        """关闭弹窗 (通用关闭按钮)。"""
        _log.info('[UI] 食堂 → 关闭弹窗')
        self._ctrl.click(*CLICK_DISMISS_POPUP)

    def click_to_skip_animation(self) -> None:
        """点击屏幕任意位置跳过动画。

        目前仅在做菜过程中使用，点击坐标为屏幕右下角。
        """
        _log.info('[UI] 食堂 → 点击跳过动画')
        self._ctrl.click(*CLICK_SKIP_ANIMATION)

    # ── 组合动作 — 做菜 ──

    _COOK_BUTTON_TIMEOUT: float = 7.5

    def cook(self, position: int = 1, *, force_cook: bool = False) -> bool:
        """选择菜谱并做菜。

        必须已在食堂页面。

        Parameters
        ----------
        position:
            菜谱编号 (1-3)。
        force_cook:
            当有菜正在生效时是否继续做菜。

        Returns
        -------
        bool
            做菜是否成功。
        """
        self.select_recipe(position)

        # 等待做菜按钮出现
        deadline = time.monotonic() + self._COOK_BUTTON_TIMEOUT
        while time.monotonic() < deadline:
            screen = self._ctrl.screenshot()
            detail = ImageChecker.find_template(screen, Templates.Cook.COOK_BUTTON)
            if detail is not None:
                self._ctrl.click(*detail.center)
                break
            time.sleep(0.3)
        else:
            raise TimeoutError(f'做菜按钮未出现 ({self._COOK_BUTTON_TIMEOUT}s)')

        time.sleep(0.5)

        # 检测 "效果正在生效" 弹窗
        screen = self._ctrl.screenshot()
        if ImageChecker.template_exists(screen, Templates.Cook.HAVE_COOK):
            if force_cook:
                self.confirm_force_cook()
                time.sleep(0.5)
                screen = self._ctrl.screenshot()
                if ImageChecker.template_exists(screen, Templates.Cook.NO_TIMES):
                    self.dismiss_popup()
                    return False
            else:
                self.cancel_force_cook()
                time.sleep(0.3)
                self.dismiss_popup()
                return False

        self.click_to_skip_animation()
        _log.info('[UI] 做菜完成 (菜谱 {})', position)

        return True
