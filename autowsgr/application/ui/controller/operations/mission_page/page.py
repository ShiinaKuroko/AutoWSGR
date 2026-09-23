"""模块功能：负责任务页面的页面检查、奖励收取和页面回退。

上层调用：
- business.logistics.reward：进入任务页面并调用完整奖励流程。
- application.ui.navigation：调用任务页面检查和回退契约。

下层依赖：
- application.ui.controller.operations.mission_page.constants：提供页面返回坐标。
- application.ui.controller.operations.mission_page.operations：提供页面原子动作。
- application.ui.controller.operations.mission_page.recognition：提供任务和奖励事实。
- application.ui.controller.operations.sortie_page.main_page：提供任务标签页检查。
- common.device.interaction：执行点击后的页面到达等待。

边界：
只编排任务页面内的奖励流程并提供导航契约，不实现识别算法、原子设备操作或跨页面调度。
"""

from __future__ import annotations

import enum
import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.mission_page import (
    constants,
    operations,
    recognition,
)
from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    TabbedPageType,
    check_tabbed_page,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.interaction import click_and_wait_for_page


if TYPE_CHECKING:
    import numpy

    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.application.ui.navigation.types import PageMatch


_log = get_logger('ui.mission_page')


# ── 奖励确认参数 ────────────────────────────────────────────────────────────────────

_REWARD_CONFIRM_TIMEOUT_SECONDS: float = 5.0
"""奖励确认弹窗的最长等待时间 (秒)。"""

_REWARD_CONFIRM_POLL_SECONDS: float = 0.3
"""奖励确认弹窗的轮询间隔 (秒)。"""

_REWARD_CONFIRM_SETTLE_SECONDS: float = 0.5
"""点击奖励确认后等待页面稳定的时间 (秒)。"""


# ── 页面标签 ──────────────────────────────────────────────────────────────────────


class MissionPanel(enum.Enum):
    """任务页面内部子标签。"""

    ALL = '全部'
    MAIN = '主线'
    DAILY = '日常'
    WEEKLY = '周常'
    TIMED = '限时'


class MissionPage:
    """任务页面的 UI 控制器。"""

    def __init__(self, ctx: UIContext) -> None:
        """保存调用方注入的 UI 上下文。

        Args:
            ctx: 提供设备控制器和 OCR 引擎的 UI 上下文。
        """
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面识别 ──────────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: numpy.ndarray) -> PageMatch:
        """判断截图是否为任务页面。

        Args:
            screen: 任务页面 RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            带标签覆盖度分数的任务页面匹配结果。
        """
        return check_tabbed_page(screen, TabbedPageType.MISSION)

    # ── 奖励收取流程 ─────────────────────────────────────────────────────────────────

    def collect_rewards(
        self,
        panel: MissionPanel = MissionPanel.ALL,
        max_scrolls: int = 6,
    ) -> bool:
        """切换面板、识别任务并收取可用奖励。

        Args:
            panel: 目标任务面板。
            max_scrolls: 允许执行的最大滚动次数。

        Returns:
            确认领取成功时返回 True，否则返回 False。

        Raises:
            ValueError: ``max_scrolls`` 小于 0。
        """
        if max_scrolls < 0:
            raise ValueError(f'max_scrolls 必须大于等于 0，收到: {max_scrolls}')

        panel_key = panel.name.lower()

        # 1. 切换到目标任务面板，等待页面内容稳定。
        operations.select_panel(self._ctrl, panel_key)
        _log.info('[UI] 任务页面 → 切换面板：目标={!r}，结果=已提交', panel_key)
        seen_names: set[str] = set()

        for scroll_index in range(max_scrolls + 1):
            # 2. 识别当前任务列表，利用重复任务判断是否需要继续滚动。
            screen = self._ctrl.screenshot()
            visible = recognition.recognize_missions(screen, self._ctx.ocr)
            new_count = 0
            for mission in visible:
                if mission.name not in seen_names:
                    seen_names.add(mission.name)
                    new_count += 1

            _log.debug(
                '[UI] 任务页面 → 识别任务：面板={!r}，滚动次数={}，任务数量={}，新增数量={}',
                panel_key,
                scroll_index,
                len(visible),
                new_count,
            )

            # 3. 领取当前页面奖励，并在同一个流程内确认弹窗终态。
            detail = recognition.find_reward_collect_all_button(screen)
            is_single_claim = detail is None
            if detail is None:
                detail = recognition.find_reward_collect_button(screen)
            claim_type = '单个领取' if is_single_claim else '一键领取'

            if detail is not None:
                _log.info('[UI] 任务页面 → {}：结果=尝试', claim_type)
                operations.click_reward_button(self._ctrl, detail.center)
                if is_single_claim:
                    time.sleep(_REWARD_CONFIRM_SETTLE_SECONDS)

                deadline = time.monotonic() + _REWARD_CONFIRM_TIMEOUT_SECONDS
                while time.monotonic() < deadline:
                    confirm = recognition.find_confirm_button(self._ctrl.screenshot())
                    if confirm is not None:
                        operations.click_confirm_button(self._ctrl, confirm.center)
                        time.sleep(_REWARD_CONFIRM_SETTLE_SECONDS)
                        _log.info('[UI] 任务页面 → {}：结果=成功', claim_type)
                        return True
                    time.sleep(_REWARD_CONFIRM_POLL_SECONDS)

                _log.error('[UI] 任务页面 → {}：结果=失败，原因=领取结果未确认', claim_type)
                return False

            if new_count == 0:
                _log.debug(
                    '[UI] 任务页面 → 停止滚动：scroll={}，原因=无新任务',
                    scroll_index,
                )
                break

            if scroll_index < max_scrolls:
                operations.scroll_task_list(self._ctrl)

        collected = False
        _log.info(
            '[UI] 任务页面 → 收取奖励：目标={!r}，结果={!r}',
            panel.value,
            '成功' if collected else '无可领取',
        )
        return collected

    # ── 页面回退 ──────────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击回退按钮, 返回主页面。

        Raises:
            NavigationError: 超时仍在任务页面。
        """
        # 主页控制器会反向引用任务页面，局部导入用于避免页面包初始化循环。
        from autowsgr.application.ui.controller.home.main_page import HomePage

        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=HomePage.check_current_page,
            source=PageName.MISSION.value,
            target=PageName.HOME.value,
        )
        _log.info('[UI] 任务页面 → 返回：目标={!r}，结果=成功', PageName.HOME.value)
