"""模块功能：负责食堂页面检查、菜谱选择、做菜弹窗和页面回退。

上层调用：
- business.logistics.cook：调用做菜入口。
- application.ui.navigation.graph.logistics：调用食堂返回后院的页面边动作。
- testing.ui：执行食堂页面导航和做菜验证。

下层依赖：
- application.ui.controller.canteen_page.constants：提供食堂页面专用坐标。
- common.ui.interaction：执行点击后的页面到达等待。
- common.vision：匹配食堂页面和做菜弹窗模板。
- common.types：提供页面名称。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.canteen_page import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page
from autowsgr.common.vision import ImageChecker, PageMatch
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('ui')

class CanteenPage:
    """食堂页面内的 UI 操作控制器。"""

    def __init__(self, ctx: GameContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面检查 ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """检查截图是否属于食堂页面。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            食堂页面匹配结果。
        """
        result = ImageChecker.find_template(screen, Templates.Page.CANTEEN, confidence=0.85)
        name = PageName.CANTEEN.value
        if result is None:
            return PageMatch(name=name, matched=False, score=0.0)
        return PageMatch(name=name, matched=True, score=result.confidence)

    # ── 页面回退 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击返回按钮，离开食堂并回到后院。

        Args:
            None.

        Raises:
            NavigationError: 超时仍未离开食堂页面。
        """
        from autowsgr.application.ui.controller.backyard_page import BackyardPage

        _log.info('[UI] 食堂 → 返回后院')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=BackyardPage.check_current_page,
            source='食堂',
            target='后院',
        )

    # ── 操作 ──────────────────────────────────────────────────────────────

    def select_recipe(self, position: int) -> None:
        """选择一个菜谱并点击其页面位置。

        Args:
            position: 菜谱编号，范围为 1-3。

        Raises:
            ValueError: 菜谱编号不在 1-3 范围内。
        """
        if position not in constants.RECIPE_POSITIONS:
            raise ValueError(f'菜谱编号必须为 1-3，收到: {position}')
        _log.info('[UI] 食堂 → 选择菜谱 {}', position)
        self._ctrl.click(*constants.RECIPE_POSITIONS[position])

    def confirm_force_cook(self) -> None:
        """确认覆盖当前生效料理并继续做菜。

        Args:
            None.

        Returns:
            None.
        """
        _log.info('[UI] 食堂 → 确认继续做菜 (覆盖生效中的菜)')
        self._ctrl.click(*constants.CLICK_FORCE_COOK)

    def cancel_force_cook(self) -> None:
        """取消覆盖当前生效料理的做菜操作。

        Args:
            None.

        Returns:
            None.
        """
        _log.info('[UI] 食堂 → 取消做菜 (保留生效中的菜)')
        self._ctrl.click(*constants.CLICK_CANCEL_COOK)

    def dismiss_popup(self) -> None:
        """关闭做菜提示弹窗。

        Args:
            None.

        Returns:
            None.
        """
        _log.info('[UI] 食堂 → 关闭弹窗')
        self._ctrl.click(*constants.CLICK_DISMISS_POPUP)

    def click_skip_animation(self) -> None:
        """点击结果动画区域，跳过做菜动画。

        Args:
            None.

        Returns:
            None.
        """
        _log.info('[UI] 食堂 → 点击跳过动画')
        self._ctrl.click(*constants.CLICK_SKIP_ANIMATION)

    # ── 组合动作 — 做菜 ──

    _COOK_BUTTON_TIMEOUT: float = 7.5

    def cook(self, position: int = 1, *, force_cook: bool = False) -> bool:
        """选择菜谱并做菜。

        Args:
            position: 菜谱编号，范围为 1-3。
            force_cook: 有料理生效时是否继续覆盖做菜。

        Returns:
            做菜是否成功；没有次数或取消覆盖时返回 ``False``。

        Raises:
            TimeoutError: 做菜按钮在等待期限内未出现。
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

        self.click_skip_animation()
        _log.info('[UI] 做菜完成 (菜谱 {})', position)

        return True
