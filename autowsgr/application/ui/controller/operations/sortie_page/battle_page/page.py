"""模块功能：执行普通出征页面的章节定位、地图确认和出征准备入口。

上层调用：
- business.combat.bettle：选择地图并进入出征准备。
- testing.ui、tools：验证章节导航和出征入口。

下层依赖：
- application.ui.controller.operations.sortie_page.battle_page.constants：提供地图数据和页面校准坐标。
- application.ui.controller.operations.sortie_page.main_page：提供 sortie_page 页面壳和顶部标签。
- application.ui.controller.operations.sortie_page.battle_page.recognition：提供章节和地图 OCR。

本文件只保留 UI 导航和面板交互；结算计数的 OCR 实现由 common 视觉模块负责。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.battle_page import (
    constants,
    recognition,
)
from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    SortiePage,
    SortieTab,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page


if TYPE_CHECKING:
    from autowsgr.application.ui.controller.operations.sortie_page.battle_page.recognition import (
        ChapterSlot,
    )
    from autowsgr.common.device import AndroidController
    from autowsgr.common.vision import OCREngine


_log = get_logger('ui')


# ── 普通出征页面流程参数 ──────────────────────────────────────────────────────

CHAPTER_NAV_MAX_ATTEMPTS = 20  # 章节导航最大尝试次数，用于限制失败循环。
CHAPTER_SLOT_CENTER_INDEX = 2  # 固定槽位中间索引，用于作为当前章节的侧栏锚点。
CHAPTER_SINGLE_STEP = 1  # 章节相邻切换步长，用于目标章节距离不足两章时选择近邻槽位。
CHAPTER_DOUBLE_STEP = 2  # 章节跨两章切换步长，用于减少普通出征侧栏翻页次数。
CHAPTER_CONFIRMATION_COUNT = 2  # 章节命中确认次数，用于避免过渡帧误判目标章节。
CHAPTER_NO_PROGRESS_LIMIT = 3  # 章节连续无进展上限，用于终止卡住的侧栏导航。
MAP_NAV_SETTLE_DELAY = 1.5000  # 章节或地图切换后的等待时间，用于避开页面动画过渡帧。
SORTIE_TAB_SETTLE_DELAY = 0.5000  # 切换到普通出征标签后的等待时间，用于等待地图面板稳定。
MAP_MAX_STUCK = 3  # 地图翻页连续无变化上限，用于重启当前地图导航尝试。
MAP_NAVIGATION_MISS_LIMIT = 6  # 地图翻页连续无法确认变化的上限，用于重启当前导航尝试。
MAP_PAGE_TRANSITION_DELAY = 0.2000  # 地图翻页额外等待时间，用于覆盖较长的节点动画。


class BattlePage(SortiePage):
    """普通出征页面控制器，直接管理章节、地图和出征准备入口。"""

    # ── 出征准备流程 ────────────────────────────────────────────────────────

    def enter_sortie(self, chapter: int | str, map_num: int | str) -> None:
        """进入出征准备页面。

        Args:
            chapter: 目标章节编号 (1-10) 或事件地图标识字符串。
            map_num: 目标地图节点编号 (1-6) 或事件地图标识字符串。

        Raises:
            ValueError: 章节或地图编号无效 (仅数字模式)。
            NavigationError: 章节导航或页面切换超时。

        Returns:
            None。页面成功进入出征准备状态后返回。
        """
        from autowsgr.application.ui.controller.fleet import BattlePreparationPage

        _log.info('[UI] 地图页面 → 进入出征 {}-{}', chapter, map_num)

        # 1. 确保在普通出征面板。
        self.select_tab(SortieTab.SORTIE)
        time.sleep(SORTIE_TAB_SETTLE_DELAY)

        # 2. 选择目标章节。
        if isinstance(chapter, int):
            max_maps = constants.CHAPTER_MAP_COUNTS.get(chapter, 0)
            if max_maps == 0:
                raise ValueError(f'章节 {chapter} 不在已知地图数据中')
            if isinstance(map_num, int) and not 1 <= map_num <= max_maps:
                raise ValueError(f'章节 {chapter} 的地图编号必须为 1-{max_maps}，收到: {map_num}')
            result = self.select_chapter(chapter)
            if result is None:
                from autowsgr.common.ui.interaction import NavigationError

                raise NavigationError(
                    f'无法导航到第 {chapter} 章',
                    screen=self._ctrl.screenshot(),
                )

        # 3. 选择目标地图节点。
        self.select_map(map_num)

        # 4. 点击进入出征准备页面并确认终态。
        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_ENTER_SORTIE,
            checker=BattlePreparationPage.check_current_page,
            source=f'地图-出征 {chapter}-{map_num}',
            target=PageName.BATTLE_PREP,
        )

    # ── 普通出征基础操作 ────────────────────────────────────────────────────

    # 章节槽位点击和 OCR 回检保持在同一导航组内，避免根据高亮条猜测点击位置。
    def click_chapter_slot(self, index: int) -> None:
        """点击一个固定章节槽位。

        Args:
            index: 当前画面中固定章节槽位的索引。

        Returns:
            None。点击请求发送到设备控制器后返回。

        Raises:
            ValueError: 槽位索引超出当前页面的固定范围。
        """
        if not 0 <= index < len(constants.CHAPTER_SLOT_POSITIONS):
            raise ValueError(
                f'章节槽位索引必须为 0-{len(constants.CHAPTER_SLOT_POSITIONS) - 1}, 收到: {index}',
            )
        position = constants.CHAPTER_SLOT_POSITIONS[index]
        self._ctrl.click(*position)
        _log.info('[UI] 地图页面→点击章节槽位 {} (x={:.3f}, y={:.3f})', index, *position)

    def select_chapter(self, target: int) -> int | None:
        """通过固定章节槽位和 OCR 回检选择目标章节。

        Args:
            target: 要选择的普通出征章节编号。

        Returns:
            已确认的章节编号；导航未取得安全点击位置或超过尝试上限时返回 ``None``。

        Raises:
            ValueError: 章节编号超出普通出征章节范围。
            RuntimeError: OCR 引擎未注入。
        """
        if not 1 <= target <= constants.TOTAL_CHAPTERS:
            raise ValueError(
                f'章节编号必须为 1-{constants.TOTAL_CHAPTERS}，收到: {target}',
            )
        if self._ocr is None:
            raise RuntimeError('需要 OCR 引擎才能导航到指定章节')

        confirm_hits = 0
        previous_current: int | None = None
        no_progress = 0

        for attempt in range(CHAPTER_NAV_MAX_ATTEMPTS):
            slots, current = _read_chapter_state(self._ctrl, self._ocr)
            slot_state = [
                slot.chapter if slot.chapter is not None else slot.text or '---' for slot in slots
            ]
            if current is None:
                _log.warning('[UI] 章节导航: 中间章节槽位识别失败 (第 {} 次尝试)', attempt + 1)
                time.sleep(MAP_NAV_SETTLE_DELAY)
                continue

            if previous_current == current:
                no_progress += 1
            else:
                no_progress = 0
            previous_current = current
            if no_progress >= CHAPTER_NO_PROGRESS_LIMIT:
                _log.warning('[UI] 章节导航: 连续无进展, 槽位={}', slot_state)
                return None

            if current == target:
                confirm_hits += 1
                _log.info(
                    '[UI] 章节导航: 命中目标第 {} 章，确认 {}/{}, 槽位={}',
                    target,
                    confirm_hits,
                    CHAPTER_CONFIRMATION_COUNT,
                    slot_state,
                )
                if confirm_hits >= CHAPTER_CONFIRMATION_COUNT:
                    _log.info('[UI] 章节导航: 已到达第 {} 章', target)
                    return current
                time.sleep(MAP_NAV_SETTLE_DELAY)
                continue

            confirm_hits = 0
            index = _calculate_chapter_slot(current, target, slots)
            if index is None:
                _log.warning(
                    '[UI] 章节导航: 目标第 {} 章没有可用槽位 (当前={}, 槽位={})',
                    target,
                    current,
                    slot_state,
                )
                time.sleep(MAP_NAV_SETTLE_DELAY)
                continue

            self.click_chapter_slot(index)
            time.sleep(MAP_NAV_SETTLE_DELAY)

        _log.warning(
            '[UI] 章节导航: 超过最大尝试次数 ({}), 目标第 {} 章',
            CHAPTER_NAV_MAX_ATTEMPTS,
            target,
        )
        return None

    def select_map(self, map_num: int | str) -> None:  # noqa: C901, PLR0912, PLR0915
        """在当前章节内翻页至目标地图节点，并通过 OCR 二次确认。

        与 :meth:`select_chapter` 采用同等强度的稳健策略:
        外层 ``CHAPTER_NAV_MAX_ATTEMPTS`` 次 attempt,
        每次多次 OCR 稳定读取当前 map_num, 每步单次 OCR 回检确认真的翻了,
        卡住 ≥2 次自动重启 attempt。

        Args:
            map_num: 当前章节内的目标地图节点编号。

        Returns:
            None。确认到达目标地图节点后返回。

        Raises:
            RuntimeError: OCR 引擎未注入，或当前地图标题无法识别。
            ValueError: 地图编号超出当前章节的已知范围，或当前章节没有地图数据。
        """
        map_num = int(map_num)
        if self._ocr is None:
            raise RuntimeError('需要 OCR 引擎才能导航到指定地图节点')
        info_probe = recognition._read_map(self._ctrl.screenshot(), self._ocr)
        if info_probe is None:
            raise RuntimeError('无法识别当前地图标题，不能校验地图编号')
        cur_max = constants.CHAPTER_MAP_COUNTS.get(int(info_probe.chapter))
        if cur_max is None:
            raise ValueError(f'当前章节 {info_probe.chapter} 不在已知地图数据中')
        if not 1 <= map_num <= cur_max:
            raise ValueError(
                f'地图编号 map_num={map_num} 超出范围 [1, {cur_max}] '
                '(若当前章识别失败请先调用 select_chapter 正确选章)',
            )
        map_nav_delay = MAP_NAV_SETTLE_DELAY

        def _read_map(
            samples: int = recognition.MAP_READ_SAMPLE_COUNT,
            delay: float = recognition.MAP_READ_SAMPLE_DELAY,
        ) -> tuple[int | None, bool]:
            """多次读取地图标题，判断当前地图编号是否稳定。

            Args:
                samples: 单轮地图标题 OCR 采样次数。
                delay: 相邻 OCR 采样之间的等待时间。

            Returns:
                当前地图编号和稳定状态；无法识别地图编号时返回 ``(None, False)``。
            """
            maps: list[int] = []
            for i in range(samples):
                screen = self._ctrl.screenshot()
                info = recognition._read_map(screen, self._ocr)
                if info is not None:
                    maps.append(info.map_num)
                if i < samples - 1:
                    time.sleep(delay)
            if not maps:
                return None, False
            if len(maps) >= recognition.MAP_READ_STABLE_COUNT and maps[-1] == maps[-2]:
                return maps[-1], True
            if len(maps) == samples and len(set(maps)) == 1:
                return maps[0], True
            candidate = max(set(maps), key=maps.count)
            _log.warning(f'[UI] 地图节点导航: OCR 抖动 {maps}, 本轮不点击')
            return candidate, False

        def _quick_map() -> int | None:
            """快速读取一次地图编号，用于确认翻页后的页面状态。"""
            screen = self._ctrl.screenshot()
            info = recognition._read_map(screen, self._ocr)
            return info.map_num if info is not None else None

        confirm = 0
        for attempt in range(CHAPTER_NAV_MAX_ATTEMPTS):
            current, stable = _read_map()
            if current is None:
                _log.warning(
                    '[UI] 地图节点导航: OCR 识别失败 (attempt %d/%d)',
                    attempt + 1,
                    CHAPTER_NAV_MAX_ATTEMPTS,
                )
                continue

            if current == map_num:
                confirm += 1
                _log.info(
                    '[UI] 地图节点导航: 命中目标 %d-%d 确认 %d/%d',
                    current,
                    map_num,
                    confirm,
                    recognition.MAP_CONFIRMATION_COUNT,
                )
                if confirm >= recognition.MAP_CONFIRMATION_COUNT:
                    _log.info(
                        '[UI] 地图节点导航: 已到达当前章第 %d 节 (地图编号 %d)', map_num, map_num
                    )
                    return
                time.sleep(map_nav_delay)
                continue

            confirm = 0
            if not stable:
                time.sleep(map_nav_delay)
                continue

            delta = map_num - current
            direction = 1 if delta > 0 else -1
            remaining = abs(delta)
            stuck = 0
            misses = 0
            steps = 0
            max_stuck = MAP_MAX_STUCK
            max_misses = MAP_NAVIGATION_MISS_LIMIT

            _log.info(
                '[UI] 地图节点导航: 当前 %d -> 目标 %d (delta=%+d)',
                current,
                map_num,
                delta,
            )

            while remaining > 0 and stuck < max_stuck and misses < max_misses:
                if direction == 1:
                    self._ctrl.click(*constants.CLICK_MAP_NEXT)
                    _log.info(
                        '[UI] 地图节点导航: → 下一节 (remaining %d, steps %d)', remaining, steps + 1
                    )
                else:
                    self._ctrl.click(*constants.CLICK_MAP_PREV)
                    _log.info(
                        '[UI] 地图节点导航: ← 上一节 (remaining %d, steps %d)', remaining, steps + 1
                    )
                steps += 1
                remaining -= 1
                time.sleep(map_nav_delay + MAP_PAGE_TRANSITION_DELAY)

                qc = _quick_map()
                if qc is None:
                    misses += 1
                    continue
                misses = 0
                if (direction == 1 and qc <= current) or (direction == -1 and qc >= current):
                    if qc == current and stuck == 0:
                        stuck = 1
                    else:
                        stuck += 1
                    _log.warning(
                        '[UI] 地图节点导航: 翻页后仍是第%d节 (cur=%d, stuck=%d/%d)',
                        qc,
                        current,
                        stuck,
                        max_stuck,
                    )
                else:
                    stuck = 0
                    current = qc
                    remaining = abs(map_num - current)
            if stuck >= max_stuck or misses >= max_misses:
                _log.warning(
                    '[UI] 地图节点导航: 卡住/识别失败超限 (stuck=%d misses=%d), 重启 attempt',
                    stuck,
                    misses,
                )
                continue

        raise RuntimeError(
            f'地图节点导航超过最大尝试次数 {CHAPTER_NAV_MAX_ATTEMPTS}, 目标节 {map_num} 未到达',
        )


# ── 章节导航内部辅助 ────────────────────────────────────────────────────────


def _read_chapter_state(
    ctrl: AndroidController,
    ocr: OCREngine,
) -> tuple[tuple[ChapterSlot, ...], int | None]:
    """从一次截图中读取章节槽位，并计算当前章节。

    Args:
        ctrl: 当前运行上下文注入的设备控制器。
        ocr: 当前运行上下文注入的 OCR 引擎。

    Returns:
        章节槽位识别结果，以及侧栏或地图标题确认出的当前章节；无法确认时为 ``None``。
    """
    screen = ctrl.screenshot()
    slots = recognition._read_chapter_slots(screen, ocr)
    title = recognition._read_map(screen, ocr)
    current = slots[CHAPTER_SLOT_CENTER_INDEX].chapter
    if current is None and title is not None:
        current = title.chapter
    if current is not None and title is not None and title.chapter != current:
        _log.warning(
            '[UI] 章节状态不一致: 侧边栏第{}章, 标题第{}章',
            current,
            title.chapter,
        )
    return slots, current


def _calculate_chapter_slot(
    current: int,
    target: int,
    slots: tuple[ChapterSlot, ...],
) -> int | None:
    """根据可见章节槽位计算普通出征的下一次点击位置。

    Args:
        current: 当前章节编号。
        target: 目标章节编号。
        slots: 当前画面可见的章节槽位识别结果。

    Returns:
        下一次应点击的章节槽位索引；没有安全点击位置时返回 ``None``。
    """
    for slot in slots:
        if slot.chapter == target:
            return slot.index

    delta = target - current
    if delta == 0:
        return None

    step = CHAPTER_DOUBLE_STEP if abs(delta) >= CHAPTER_DOUBLE_STEP else CHAPTER_SINGLE_STEP
    direction = 1 if delta > 0 else -1
    index = CHAPTER_SLOT_CENTER_INDEX + direction * step
    if not 0 <= index < len(slots):
        return None

    expected = current + direction * step
    return index if slots[index].chapter == expected else None
