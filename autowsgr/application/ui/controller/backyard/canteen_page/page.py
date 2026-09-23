"""模块功能：负责食堂页面识别、菜谱选择、做菜弹窗和返回后院。

上层调用：
- business.logistics.cook：调用做菜入口。
- application.ui.navigation.registry：注册食堂页面识别器。
- application.ui.navigation.graph.logistics：调用食堂返回后院的页面边动作。
- testing.ui：执行食堂页面识别和返回后院验证。

下层依赖：
- application.ui.controller.backyard.canteen_page.constants：提供页面坐标。
- common.device.interaction：执行点击后的页面到达等待。
- common.vision、common.vision.resources：提供页面和弹窗识别。
- common.types：提供页面名称。

本模块只编排食堂页面内的 UI 检查、点击和页面回退，不负责跨页面寻路、业务任务调度或运行时上下文创建。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.backyard.canteen_page import constants, operations
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.interaction import click_and_wait_for_page
from autowsgr.common.vision import ImageChecker, PageMatch
from autowsgr.application.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.controller.context import UIContext


_log = get_logger('ui.backyard.canteen_page')

# ── 做菜流程参数 ─────────────────────────────────────────────────────────────

_COOK_BUTTON_TIMEOUT_SECONDS = 7.5  # 等待做菜按钮出现的最长时间。
_COOK_BUTTON_POLL_INTERVAL_SECONDS = 0.3  # 轮询做菜按钮的间隔。
_COOK_TRANSITION_WAIT_SECONDS = 0.5  # 点击做菜或确认覆盖后的页面过渡时间。
_CANCEL_POPUP_WAIT_SECONDS = 0.3  # 取消覆盖后等待弹窗关闭的时间。


class CanteenPage:
    """食堂页面内的 UI 操作控制器。"""

    def __init__(self, ctx: UIContext) -> None:
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

    # ── 做菜流程 ────────────────────────────────────────────────────────────

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
        if position not in constants.RECIPE_POSITIONS:
            _log.error(
                '[UI] 食堂 → 拒绝做菜：菜谱位置={}，期望范围=1..3，结果=拒绝',
                position,
            )
            raise ValueError(f'菜谱编号必须为 1-3，收到: {position}')
        _log.info(
            '[UI] 食堂 → 做菜：菜谱位置={}，强制覆盖={!r}，状态=开始',
            position,
            force_cook,
        )
        # 1. 选择目标菜谱。
        operations.click_recipe(self._ctrl, constants.RECIPE_POSITIONS[position])

        # 2. 等待做菜按钮出现。
        deadline = time.monotonic() + _COOK_BUTTON_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            screen = self._ctrl.screenshot()
            detail = ImageChecker.find_template(screen, Templates.Cook.COOK_BUTTON)
            if detail is not None:
                operations.click_cook_button(self._ctrl, detail.center)
                break
            time.sleep(_COOK_BUTTON_POLL_INTERVAL_SECONDS)
        else:
            _log.error(
                '[UI] 食堂 → 做菜超时：菜谱位置={}，超时={:.1f}s，'
                '原因=做菜按钮未出现，结果=失败',
                position,
                _COOK_BUTTON_TIMEOUT_SECONDS,
            )
            raise TimeoutError(f'做菜按钮未出现 ({_COOK_BUTTON_TIMEOUT_SECONDS}s)')

        time.sleep(_COOK_TRANSITION_WAIT_SECONDS)

        # 3. 检测“效果正在生效”弹窗并决定覆盖或取消。
        screen = self._ctrl.screenshot()
        has_active_cook = ImageChecker.template_exists(screen, Templates.Cook.HAVE_COOK)
        _log.debug(
            '[UI] 食堂 → 判断覆盖：菜谱位置={}，强制覆盖={!r}，已有料理={!r}',
            position,
            force_cook,
            has_active_cook,
        )
        if has_active_cook:
            if force_cook:
                operations.click_force_cook(self._ctrl)
                time.sleep(_COOK_TRANSITION_WAIT_SECONDS)
                screen = self._ctrl.screenshot()
                no_times = ImageChecker.template_exists(screen, Templates.Cook.NO_TIMES)
                _log.debug('[UI] 食堂 → 判断次数：菜谱位置={}，次数不足={!r}', position, no_times)
                if no_times:
                    operations.click_dismiss_popup(self._ctrl)
                    _log.warning(
                        '[UI] 食堂 → 做菜失败：菜谱位置={}，强制覆盖={!r}，'
                        '原因=次数不足，结果=失败',
                        position,
                        force_cook,
                    )
                    return False
            else:
                operations.click_cancel_cook(self._ctrl)
                time.sleep(_CANCEL_POPUP_WAIT_SECONDS)
                operations.click_dismiss_popup(self._ctrl)
                _log.info(
                    '[UI] 食堂 → 取消做菜：菜谱位置={}，原因=已有料理，结果=已取消',
                    position,
                )
                return False

        # 4. 跳过结果动画，完成做菜流程。
        operations.click_skip_animation(self._ctrl)
        _log.info(
            '[UI] 食堂 → 做菜：菜谱位置={}，强制覆盖={!r}，结果=已提交',
            position,
            force_cook,
        )

        return True

    # ── 返回后院 ────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击返回按钮，离开食堂并回到后院。

        Raises:
            NavigationError: 超时仍未离开食堂页面。
        """
        # 延迟导入，避免后院页面的食堂目标检查形成循环导入。
        from autowsgr.application.ui.controller.backyard.main_page import BackyardPage

        _log.info('[UI] 食堂 → 回后院：目标={!r}，状态=开始', PageName.BACKYARD.value)
        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=BackyardPage.check_current_page,
            source='食堂',
            target=PageName.BACKYARD,
        )
        _log.info('[UI] 食堂 → 回后院：目标={!r}，结果=成功', PageName.BACKYARD.value)
