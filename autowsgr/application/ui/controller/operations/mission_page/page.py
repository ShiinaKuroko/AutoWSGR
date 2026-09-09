"""模块功能：负责任务页面的页面检查、标签切换、奖励收取和页面回退。

上层调用：
- business.logistics.reward：进入任务页面并调用奖励收取和任务识别。
- application.ui.navigation.graph.logistics：调用页面回退动作返回母港主页。
- testing.ui：验证任务页面识别、标签切换和页面回退。

下层依赖：
- application.ui.controller.operations.mission_page.constants：提供页面坐标和时序参数。
- application.ui.controller.operations.mission_page.recognition：提供任务库、按钮扫描和 OCR 识别。
- application.ui.controller.shared.top_tabs：检查任务标签页。
- common.ui.interaction：执行点击后的页面到达等待。
- common.vision：匹配任务页面和奖励确认弹窗。

页面控制器只负责任务页面内的 UI 行为；任务数据模型和 OCR 规则归属 recognition.py。
"""

from __future__ import annotations

import enum
import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.mission_page import constants
from autowsgr.application.ui.controller.operations.mission_page.recognition import (
    find_button_rows,
    get_all_mission_names,
    recognize_row,
)
from autowsgr.application.ui.controller.shared.top_tabs import TabbedPageType, check_tabbed_page
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page
from autowsgr.common.vision import ImageChecker, PageMatch
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext
    from autowsgr.application.ui.controller.operations.mission_page.recognition import MissionInfo


_log = get_logger('ui')


# ── 页面标签 ────────────────────────────────────────────────────────────────


class MissionPanel(enum.Enum):
    """任务页面内部子标签。"""

    ALL = '全部'
    MAIN = '主线'
    DAILY = '日常'
    WEEKLY = '周常'
    TIMED = '限时'


PANEL_LIST: list[MissionPanel] = list(MissionPanel)
"""任务页面可切换的子标签，按页面显示顺序排列。"""

CLICK_PANEL: dict[MissionPanel, tuple[float, float]] = {
    panel: constants.PANEL_POSITIONS[panel.name.lower()] for panel in MissionPanel
}
"""任务页面子标签点击位置，按标签枚举提供页面动作使用。"""


class MissionPage:
    """任务页面控制器。

    Parameters
    ----------
    ctx:
        游戏上下文实例。
    """

    def __init__(self, ctx: GameContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面识别 ──────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否为任务页面 (返回带覆盖度分数的 PageMatch)。"""
        return check_tabbed_page(screen, TabbedPageType.MISSION)

    # ── 面板切换 ──────────────────────────────────────────────────────────

    def select_panel(self, panel: MissionPanel) -> None:
        """切换到指定子标签 (日常/周常)。

        Parameters
        ----------
        panel:
            目标面板。
        """
        _log.info('[UI] 任务页面: 切换到 {}', panel.value)
        self._ctrl.click(*CLICK_PANEL[panel])
        time.sleep(constants.PANEL_SWITCH_DELAY)

    # ── 任务识别 ──────────────────────────────────────────────────────────

    def read_missions(self, screen: np.ndarray) -> list[MissionInfo]:
        """识别截图中可见的任务列表 (单帧, 不滚动)。

        Parameters
        ----------
        screen:
            任务页面截图 (HxWx3, RGB)。

        Returns
        -------
        list[MissionInfo]
            可见任务列表, 按从上到下排列。
        """
        rows = find_button_rows(screen)
        if not rows:
            _log.debug('[UI] 任务页面: 未检测到按钮行')
            return []

        candidates = get_all_mission_names()
        missions: list[MissionInfo] = []
        for anchor_y, btn_type in rows:
            info = recognize_row(screen, anchor_y, btn_type, self._ctx.ocr, candidates)
            if info is None:
                _log.debug('[UI] 任务识别: 跳过无效行 (anchor_y={:.3f})', anchor_y)
                continue
            _log.debug(
                '[UI] 任务识别: {} (raw={!r}, progress={}%, claimable={})',
                info.name,
                info.raw_text,
                info.progress,
                info.claimable,
            )
            missions.append(info)
        return missions

    def read_all_missions(
        self,
        panel: MissionPanel = MissionPanel.DAILY,
        max_scrolls: int = 6,
    ) -> list[MissionInfo]:
        """识别指定子标签下的全部任务 (含自动滚动)。

        Parameters
        ----------
        panel:
            子标签: ``MissionPanel.DAILY`` 或 ``MissionPanel.WEEKLY``。
        max_scrolls:
            最大滚动次数。

        Returns
        -------
        list[MissionInfo]
            全部任务列表。
        """
        self.select_panel(panel)

        all_missions: list[MissionInfo] = []
        seen_names: set[str] = set()

        for _scroll in range(max_scrolls + 1):
            screen = self._ctrl.screenshot()
            visible = self.read_missions(screen)
            new_count = 0
            for m in visible:
                if m.name not in seen_names:
                    seen_names.add(m.name)
                    all_missions.append(m)
                    new_count += 1
            if new_count == 0:
                _log.debug('[UI] 任务识别: 无新任务, 停止滚动 (第 {} 次)', _scroll)
                break
            # 向下滑动
            self._ctrl.swipe(*constants.SCROLL, duration=constants.SCROLL_DURATION)
            time.sleep(constants.SCROLL_DELAY)

        _log.info('[UI] 任务识别完成: {} 条 (panel={})', len(all_missions), panel.value)
        return all_missions

    # ── 奖励收取 ─────────────────────────────────────────────────────────

    def collect_rewards(self) -> bool:
        """在任务页面收取奖励。

        必须已在任务页面。依次尝试一键领取和单个领取。

        Returns
        -------
        bool
            是否成功领取并确认了奖励。
        """
        # 尝试 "一键领取"
        screen = self._ctrl.screenshot()
        detail = ImageChecker.find_template(screen, Templates.GameUI.REWARD_COLLECT_ALL)
        if detail is not None:
            self._ctrl.click(*detail.center)
            return self._try_confirm(timeout=5.0)

        # 尝试 "单个领取"
        screen = self._ctrl.screenshot()
        detail = ImageChecker.find_template(screen, Templates.GameUI.REWARD_COLLECT)
        if detail is not None:
            self._ctrl.click(*detail.center)
            time.sleep(0.5)
            self._try_confirm(timeout=5.0)
            return True

        return False

    # ── 页面回退 ──────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击回退按钮, 返回主页面。

        Raises
        ------
        NavigationError
            超时仍在任务页面。
        """
        from autowsgr.application.ui.controller.home.main_page import HomePage

        _log.info('[UI] 任务页面 -> 返回主页面')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=HomePage.check_current_page,
            source=PageName.MISSION,
            target=PageName.HOME,
        )

    # ── 私有确认辅助 ─────────────────────────────────────────────────────

    def _try_confirm(self, *, timeout: float = 5.0) -> bool:
        """等待并点击确认弹窗。

        领取后弹窗可能延迟出现, 轮询等待 :data:`Templates.Confirm` 模板,
        命中即点击按钮中心关闭弹窗; 超时返回 ``False`` (未弹窗或已关闭)。
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            screen = self._ctrl.screenshot()
            detail = ImageChecker.find_any(screen, Templates.Confirm.all())
            if detail is not None:
                self._ctrl.click(*detail.center)
                time.sleep(0.5)
                return True
            time.sleep(0.3)
        return False
