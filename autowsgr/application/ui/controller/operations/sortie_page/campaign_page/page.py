"""模块功能：执行地图战役面板的次数读取、难度切换和出征准备入口。

上层调用：
- business.combat.campaign：选择战役并进入出征准备。
- testing.business、testing.ui：验证战役次数、难度和入口流程。

下层依赖：
- application.ui.controller.operations.sortie_page.battle_page.base：提供面板切换和页面上下文。
- application.ui.controller.operations.sortie_page.campaign_page.constants：提供战役坐标和颜色校准。
- application.ui.controller.operations.sortie_page.campaign_page.recognition：提供战役 OCR 结果。
- common.vision：读取难度状态和执行页面动作。
"""

from __future__ import annotations

import time

from autowsgr.application.ui.controller.operations.sortie_page.battle_page.base import BaseMapPage
from autowsgr.application.ui.controller.operations.sortie_page.battle_page.data import MapPanel
from autowsgr.application.ui.controller.operations.sortie_page.campaign_page import constants
from autowsgr.application.ui.controller.operations.sortie_page.campaign_page.recognition import (
    AcquisitionCounts,
    recognize_acquisition_counts,
    recognize_campaign_remains,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import wait_for_page
from autowsgr.common.vision import Color, PixelChecker


_log = get_logger('ui')
_DIFFICULTY_EASY_COLOR = Color.from_rgb_tuple(constants.DIFFICULTY_EASY_COLOR)
_DIFFICULTY_HARD_COLOR = Color.from_rgb_tuple(constants.DIFFICULTY_HARD_COLOR)


class CampaignPanelMixin(BaseMapPage):
    """Mixin: 战役面板操作 — 难度识别 / 切换 / 进入战役。"""

    AcquisitionCounts = AcquisitionCounts

    # ── 查询 ─────────────────────────────────────────────────────────────

    def read_campaign_remains(self) -> tuple[int, int] | None:
        """读取战役剩余次数和总次数。

        Returns:
            ``(剩余次数, 总次数)``；OCR 无法匹配时返回 ``None``。
        """
        self.ensure_panel(MapPanel.BATTLE)
        time.sleep(0.5)
        screen = self._ctrl.screenshot()
        return recognize_campaign_remains(screen, self._ocr)

    def read_difficulty(self) -> str | None:
        """通过难度按钮颜色读取当前难度。

        Returns:
            ``"easy"`` 或 ``"hard"``。

        Raises:
            RuntimeError: 重试后仍无法识别难度。
        """
        retry = 0
        while retry < 10:
            screen = self._ctrl.screenshot()
            px = PixelChecker.get_pixel(screen, *constants.CLICK_DIFFICULTY)
            if px.near(_DIFFICULTY_EASY_COLOR, tolerance=constants.DIFFICULTY_EASY_TOLERANCE):
                return 'hard'
            elif px.near(_DIFFICULTY_HARD_COLOR, tolerance=constants.DIFFICULTY_HARD_TOLERANCE):
                return 'easy'
            time.sleep(0.25)
            retry += 1

        _log.warning('[UI] 无法识别难度: 检测点颜色不匹配简单或困难')
        raise RuntimeError('无法识别战役难度')

    def read_acquisition_counts(self) -> AcquisitionCounts:
        """读取今日舰船和战利品获取数量。

        Returns:
            获取数量结果；无法识别的字段为 ``None``。
        """
        self.ensure_panel(MapPanel.SORTIE)
        time.sleep(0.5)
        screen = self._ctrl.screenshot()
        return recognize_acquisition_counts(screen, self._ocr)

    # ── 操作 ─────────────────────────────────────────────────────────────

    def enter_campaign(
        self,
        map_index: int = 2,
        difficulty: str = 'hard',
        campaign_name: str = '未知',
    ) -> None:
        """选择战役难度和类型，并进入出征准备页面。

        Args:
            map_index: 战役编号，范围为 1-5。
            difficulty: 目标难度，只能是 ``"easy"`` 或 ``"hard"``。
            campaign_name: 仅用于日志的战役名称。

        Raises:
            ValueError: 战役编号或难度无效。
            NavigationError: 超时未到达出征准备页面。
        """
        from autowsgr.application.ui.controller.battle_preparation import BattlePreparationPage

        if map_index not in constants.CAMPAIGN_POSITIONS:
            raise ValueError(f'战役编号必须为 1-5，收到: {map_index}')
        if difficulty not in ('easy', 'hard'):
            raise ValueError(f'难度必须为 easy 或 hard，收到: {difficulty}')

        _log.info(
            '[UI] 地图页面 → 进入战役 {} ({})',
            campaign_name,
            difficulty,
        )

        # 1. 切换到战役面板
        self.ensure_panel(MapPanel.BATTLE)

        # 2. 选择难度
        if self.read_difficulty() != difficulty:
            self._ctrl.click(*constants.CLICK_DIFFICULTY)
        while self.read_difficulty() != difficulty:
            _log.debug('[UI] 等待难度切换到 {}…', difficulty)
            time.sleep(0.25)
        time.sleep(0.75)

        # 3. 选择战役
        self._ctrl.click(*constants.CAMPAIGN_POSITIONS[map_index])
        time.sleep(0.5)

        # 等待到达出征准备
        wait_for_page(
            self._ctrl,
            checker=BattlePreparationPage.check_current_page,
            source=f'地图-战役 {campaign_name}',
            target=PageName.BATTLE_PREP,
        )
