"""模块功能：执行演习页面的对手状态读取、选择、刷新和出征准备操作。

上层调用：
- business.combat.exercise：选择可挑战对手并进入演习准备。
- testing.ui、testing.business：验证对手列表和阵容识别。

下层依赖：
- application.ui.controller.operations.sortie_page.main_page：提供 sortie_page 页面壳和顶部标签。
- application.ui.controller.operations.sortie_page.exercise_page.constants：提供演习坐标和颜色校准。
- common.vision：读取对手按钮和阵容状态。

演习面板共有 5 个对手，屏幕一次显示 4 个；读取和选择时通过上下滑动
分别访问对手 1-4 和对手 5。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.exercise_page import constants
from autowsgr.application.ui.controller.operations.sortie_page.main_page import SortiePage
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page
from autowsgr.common.vision import Color, PixelChecker


if TYPE_CHECKING:
    import numpy as np


_log = get_logger('ui')
_ARROW_GRAY = Color.from_rgb_tuple(constants.ARROW_GRAY)
_CHALLENGE_COLOR = Color.from_rgb_tuple(constants.CHALLENGE_COLOR)

# ── 对手状态模型 ────────────────────────────────────────────────────────────


@dataclass
class ExerciseRivalStatus:
    """保存五个演习对手的可挑战状态。"""

    rivals: list[bool] = field(default_factory=lambda: [False] * 5)

    @property
    def challengeable_count(self) -> int:
        """可挑战的对手数量。"""
        return sum(self.rivals)

    def first_challengeable(self) -> int | None:
        """返回第一个可挑战对手的序号 (1-based)，无则返回 ``None``。"""
        for i, ok in enumerate(self.rivals):
            if ok:
                return i + 1
        return None

    def __repr__(self) -> str:
        tags = ['Y' if ok else 'N' for ok in self.rivals]
        return f'ExerciseRivalStatus([{", ".join(tags)}])'


# ── 演习面板控制器 ──────────────────────────────────────────────────────────


class ExercisePage(SortiePage):
    """演习页面控制器，直接管理对手状态、选择、刷新和出征准备。

    所有方法假设调用前已处于演习顶部标签。
    """

    # ── 对手状态 ────────────────────────────────────────────────────────────

    def read_exercise_rival_status(self) -> ExerciseRivalStatus:
        """读取 5 个演习对手的可挑战状态。

        Returns:
            五个对手的状态，索引 0-4 对应对手 1-5。
        """
        status = ExerciseRivalStatus()

        # 1. 确保在顶部
        screen = self._ctrl.screenshot()
        if not self._check_exercise_at_top(screen):
            self._exercise_swipe_to_top()
            screen = self._ctrl.screenshot()

        # 2. 读取对手 1-4
        for i in range(4):
            status.rivals[i] = self._check_challenge_at(screen, i)

        _log.debug(
            '[UI] 演习对手 1-4 状态: {}',
            ['Y' if s else 'N' for s in status.rivals[:4]],
        )

        # 3. 下滑到底部
        self._exercise_swipe_to_bottom()
        screen = self._ctrl.screenshot()

        # 4. 读取对手 5 (此时在第 4 个可见位置)
        status.rivals[4] = self._check_challenge_at(screen, 3)

        _log.info('[UI] 演习对手状态: {}', status)
        return status

    # ── 对手选择 ────────────────────────────────────────────────────────────

    def select_exercise_rival(self, rival_index: int) -> None:
        """选择指定演习对手并进入对手信息页面。

        Args:
            rival_index: 对手序号，范围为 1-5。

        Raises:
            ValueError: 对手序号不在 1-5 范围内。
        """
        if not 1 <= rival_index <= 5:
            raise ValueError(f'对手序号必须为 1-5，收到: {rival_index}')

        _log.info('[UI] 演习 → 选择第 {} 个对手', rival_index)

        if rival_index <= 4:
            # 对手 1-4: 确保在顶部
            screen = self._ctrl.screenshot()
            if not self._check_exercise_at_top(screen):
                self._exercise_swipe_to_top()

            slot = rival_index - 1  # 可见位置 0-3
            x, y = constants.CHALLENGE_PROBES[slot]
            self._ctrl.click(x, y)
        else:
            # 对手 5: 确保在底部
            screen = self._ctrl.screenshot()
            if not self._check_exercise_at_bottom(screen):
                self._exercise_swipe_to_bottom()

            x, y = constants.CHALLENGE_PROBES[3]  # 第 4 个可见位置
            self._ctrl.click(x, y)

        time.sleep(0.5)

    # ── 出征准备入口 ────────────────────────────────────────────────────────

    def enter_exercise_battle(self) -> None:
        """在「对手信息」页面点击开始战斗，进入出征准备页。

        Args:
            None.

        Raises:
            NavigationError: 超时未到达出征准备页面。
        """
        from autowsgr.application.ui.controller.fleet import BattlePreparationPage

        _log.info('[UI] 演习 → 开始战斗 (对手信息页 → 出征准备)')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_START_BATTLE,
            checker=BattlePreparationPage.check_current_page,
            source='演习-对手信息',
            target=PageName.BATTLE_PREP,
        )
        self._ctx.ui_stack.push(PageName.BATTLE_PREP)

    # ── 对手信息刷新 ────────────────────────────────────────────────────────

    def refresh_rival_in_info_page(self) -> None:
        """在对手信息页面点击刷新按钮，更换当前对手阵容。"""
        _log.info('[UI] 演习 → 刷新对手阵容 (对手信息页)')
        self._ctrl.click(*constants.CLICK_RIVAL_INFO)
        time.sleep(0.75)

    # ── 对手阵容读取 ────────────────────────────────────────────────────────

    def read_rival_formation(self) -> list[str] | None:
        """读取对手阵容接口；当前未实现 OCR，始终返回 ``None``。

        Returns:
            对手舰船类型列表；当前实现固定返回 ``None``。
        """
        screen = self._ctrl.screenshot()
        _log.debug('[UI] 演习 → 识别对手阵容 (预留接口, 尚未实现)')
        # TODO: 实现 OCR 识别对手阵容
        # 参考 legacy get_enemy_condition() — 裁切 TYPE_SCAN_AREA[0] 区域进行文字识别
        _ = screen
        return None

    # ── 组合操作 ────────────────────────────────────────────────────────────

    def challenge_rival(self, rival_index: int) -> None:
        """选择指定对手并直接进入出征准备页。

        Args:
            rival_index: 对手序号，范围为 1-5。
        """
        self.select_exercise_rival(rival_index)
        time.sleep(0.5)
        self.enter_exercise_battle()

    # ── 私有辅助：列表位置和按钮状态 ────────────────────────────────────────

    def _check_exercise_at_top(self, screen: np.ndarray) -> bool:
        """检查演习列表是否位于顶部。"""
        return PixelChecker.check_pixel(
            screen,
            *constants.ARROW_UP_PROBE,
            _ARROW_GRAY,
            constants.ARROW_TOLERANCE,
        )

    def _check_exercise_at_bottom(self, screen: np.ndarray) -> bool:
        """检查演习列表是否位于底部。"""
        return PixelChecker.check_pixel(
            screen,
            *constants.ARROW_DOWN_PROBE,
            _ARROW_GRAY,
            constants.ARROW_TOLERANCE,
        )

    def _exercise_swipe_to_top(self) -> None:
        """将演习列表滑动到顶部并等待列表稳定。"""
        self._ctrl.swipe(*constants.SWIPE_TO_TOP)
        time.sleep(constants.SWIPE_DELAY)

    def _exercise_swipe_to_bottom(self) -> None:
        """将演习列表滑动到底部并等待列表稳定。"""
        self._ctrl.swipe(*constants.SWIPE_TO_BOTTOM)
        time.sleep(constants.SWIPE_DELAY)

    def _check_challenge_at(self, screen: np.ndarray, slot: int) -> bool:
        """检查可见位置上的演习挑战按钮状态。"""
        x, y = constants.CHALLENGE_PROBES[slot]
        return PixelChecker.check_pixel(
            screen,
            x,
            y,
            _CHALLENGE_COLOR,
            constants.CHALLENGE_TOLERANCE,
        )
