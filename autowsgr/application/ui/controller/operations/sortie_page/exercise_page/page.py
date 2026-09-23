"""模块功能：编排演习对手读取、刷新和挑战流程。

上层调用：
- business.combat.exercise：读取可挑战对手并执行演习挑战。
- testing.ui、testing.business：验证页面入口和对手状态结果。

下层依赖：
- application.ui.controller.operations.sortie_page.main_page：提供 sortie_page 页面壳。
- application.ui.controller.operations.sortie_page.exercise_page.recognition：读取页面视觉事实。
- application.ui.controller.operations.sortie_page.exercise_page.operations：执行页面原子操作。
- common.device.interaction、common.types：提供导航等待和页面名称契约。

边界：
本模块只持有调用方注入的 UI 上下文并编排演习页面流程，不实现像素识别或设备操作细节。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from autowsgr.application.ui.controller.operations.sortie_page.exercise_page import (
    operations,
    recognition,
)
from autowsgr.application.ui.controller.operations.sortie_page.main_page import SortiePage
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.interaction import NavigationError, wait_for_page


_log = get_logger('ui.sortie.exercise_page')


# ── 页面流程参数 ────────────────────────────────────────────────────────────

_RIVAL_INFO_SETTLE_DELAY = 1.0  # 选择对手后等待对手信息页稳定的时间（秒）。
_RIVAL_REFRESH_SETTLE_DELAY = 0.75  # 刷新对手后等待阵容更新的时间（秒）。


@dataclass
class ExerciseRivalStatus:
    """保存五个演习对手的可挑战状态。"""

    rivals: list[bool] = field(default_factory=lambda: [False] * 5)

    @property
    def challengeable_count(self) -> int:
        """返回可挑战的对手数量。

        Returns:
            可挑战的对手数量。
        """
        return sum(self.rivals)

    def first_challengeable(self) -> int | None:
        """返回第一个可挑战对手的序号。

        Returns:
            第一个可挑战对手的 1-based 序号；没有可挑战对手时返回 None。
        """
        for index, challengeable in enumerate(self.rivals, start=1):
            if challengeable:
                return index
        return None


# ── 对手状态读取 ───────────────────────────────────────────────────────────


class ExercisePage(SortiePage):
    """演习页面控制器，提供对手状态读取、刷新和挑战入口。"""

    def read_exercise_rival_status(self) -> ExerciseRivalStatus:
        """读取五个演习对手的可挑战状态。

        Returns:
            五个对手的状态，列表索引 0-4 对应对手序号 1-5。
        """
        status = ExerciseRivalStatus()

        # 1. 先把列表定位到顶部，保证首屏对应对手 1-4。
        screen = self._ctrl.screenshot()
        at_top = recognition.check_rival_list_at_top(screen)
        _log.debug(
            '[UI] 演习对手列表 → 定位：期望位置={!r}，匹配={!r}',
            '顶部',
            at_top,
        )
        if not at_top:
            operations.swipe_rival_list_to_top(self._ctrl)
            screen = self._ctrl.screenshot()

        # 2. 读取首屏的四个可见对手。
        for visible_slot in range(4):
            status.rivals[visible_slot] = recognition.check_rival_challenge_available(
                screen,
                visible_slot,
            )
        _log.debug(
            '[UI] 演习对手 → 读取：对手状态={!r}，可见槽位={!r}',
            tuple(status.rivals[:4]),
            (1, 2, 3, 4),
        )

        # 3. 下滑到底部，准备读取最后一个对手。
        operations.swipe_rival_list_to_bottom(self._ctrl)
        screen = self._ctrl.screenshot()

        # 4. 最后一个对手位于底部首屏的第 4 个可见槽位。
        status.rivals[4] = recognition.check_rival_challenge_available(screen, 3)
        _log.debug(
            '[UI] 演习对手 → 读取：对手状态={!r}，可挑战数量={}，结果=成功',
            tuple(status.rivals),
            status.challengeable_count,
        )
        return status

    # ── 对手挑战流程 ────────────────────────────────────────────────────────

    def challenge_rival(
        self,
        rival_index: int,
        *,
        refresh_rival: bool = False,
    ) -> None:
        """选择指定演习对手并进入出征准备页。

        Args:
            rival_index: 对手序号，范围为 1-5。
            refresh_rival: 是否在选择对手前刷新当前对手阵容。

        Raises:
            ValueError: 对手序号不在 1-5 范围内。
            NavigationError: 点击开始战斗后未确认进入出征准备页。
        """
        # 1. 校验业务输入，避免使用无效槽位操作设备。
        if not isinstance(rival_index, int) or not 1 <= rival_index <= 5:
            raise ValueError(f'对手序号必须为 1-5，收到: {rival_index!r}')

        _log.info(
            '[UI] 演习 → 挑战对手：对手序号={}，刷新对手={!r}，状态=开始',
            rival_index,
            refresh_rival,
        )

        # 2. 按参数刷新当前对手阵容，等待信息页稳定。
        if refresh_rival:
            _log.info('[UI] 演习 → 刷新对手：状态=开始')
            operations.click_rival_refresh(self._ctrl)
            time.sleep(_RIVAL_REFRESH_SETTLE_DELAY)
            _log.info('[UI] 演习 → 刷新对手：结果=已提交')

        # 3. 定位目标对手，必要时先把列表滑到对应位置。
        expected_at_top = rival_index <= 4
        screen = self._ctrl.screenshot()
        matched = (
            recognition.check_rival_list_at_top(screen)
            if expected_at_top
            else recognition.check_rival_list_at_bottom(screen)
        )
        expected_position = 'top' if expected_at_top else 'bottom'
        _log.debug(
            '[UI] 演习对手列表 → 定位：对手序号={}，期望位置={!r}，匹配={!r}',
            rival_index,
            expected_position,
            matched,
        )
        if not matched:
            if expected_at_top:
                operations.swipe_rival_list_to_top(self._ctrl)
            else:
                operations.swipe_rival_list_to_bottom(self._ctrl)

        visible_slot = rival_index - 1 if expected_at_top else 3
        operations.click_rival(self._ctrl, visible_slot)
        time.sleep(_RIVAL_INFO_SETTLE_DELAY)

        # 4. 点击开始战斗并确认进入出征准备页。
        # 局部导入避免舰队页面包与 sortie 页面包初始化时形成循环依赖。
        from autowsgr.application.ui.controller.fleet import BattlePreparationPage

        target = PageName.BATTLE_PREP.value
        _log.info('[UI] 演习 → 开始战斗：目标={!r}，状态=开始', target)
        try:
            operations.click_start_battle(self._ctrl)
            wait_for_page(
                self._ctrl,
                checker=BattlePreparationPage.check_current_page,
                source='演习对手信息',
                target=target,
            )
        except NavigationError as exc:
            _log.opt(exception=True).error(
                '[UI] 演习 → 终止：动作={!r}，目标={!r}，错误类型={!r}，'
                '错误={!r}，结果=失败，下一步=抛出异常',
                '进入出征准备',
                target,
                type(exc).__name__,
                str(exc),
            )
            raise

        self._ctx.ui_stack.push(PageName.BATTLE_PREP)
        _log.info('[UI] 演习 → 开始战斗：目标={!r}，结果=成功', target)

        # 5. 报告完整挑战流程已确认完成。
        _log.info(
            '[UI] 演习 → 挑战对手：对手序号={}，结果=成功',
            rival_index,
        )
