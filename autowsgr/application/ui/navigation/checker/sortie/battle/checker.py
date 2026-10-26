"""模块功能：确认出征页章节事实，并确保选中目标章节与地图节点。

上层调用：
- application.ui.navigation.service：导航到出征页的指定章节时调用 ensure_chapter。
- application.ui.navigation.registry：把章节事实入口用作页面内到达确认。

下层依赖：
- checker.sortie.battle.constants：提供地图数据与章节范围。
- checker.sortie.battle.recognition：读取章节与地图事实。
- controller.operations.sortie_page：执行标签、章节槽位与地图翻页的单次点击。
- common.system.logger：记录导航事实与失败原因。

边界：本模块拥有「选到第 X 章第 Y 节」的业务流程与落点计算；不截图、不 OCR、
不做跨页面导航、不决定业务是否继续。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.battle_page import BattlePage
from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    SortiePage,
    SortieTab,
)
from autowsgr.application.ui.navigation.checker.sortie import check_sortie_page
from autowsgr.application.ui.navigation.checker.sortie.battle import constants, recognition
from autowsgr.application.ui.navigation.types import NavigationError
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Sequence

    from autowsgr.application.ui.navigation.checker.sortie.battle.recognition import ChapterSlot
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 章节导航参数 ─────────────────────────────────────────────────────────────

# 章节与地图节点的最大尝试次数，用于限制失败循环。
CHAPTER_NAV_MAX_ATTEMPTS = 20
# 章节命中确认次数，用于避免过渡帧误判目标章节。
CHAPTER_CONFIRMATION_COUNT = 2
# 章节连续无进展上限，用于终止卡住的侧栏导航。
CHAPTER_NO_PROGRESS_LIMIT = 3
# 章节相邻切换步长与跨两章切换步长。
CHAPTER_SINGLE_STEP = 1
CHAPTER_DOUBLE_STEP = 2
# 章节或地图切换后的等待时间，用于避开页面动画过渡帧。
MAP_NAV_SETTLE_DELAY = 1.5000
# 地图标题单轮 OCR 采样次数与采样间隔。
MAP_READ_SAMPLE_COUNT = 3
MAP_READ_SAMPLE_DELAY = 0.1500
# 地图标题连续相同采样次数，用于判定当前地图稳定。
MAP_READ_STABLE_COUNT = 2
# 目标地图 OCR 命中确认次数，用于避免过渡帧误判地图节点。
MAP_CONFIRMATION_COUNT = 2
# 地图翻页连续无变化上限与识别失败上限。
MAP_MAX_STUCK = 3
MAP_NAVIGATION_MISS_LIMIT = 6
# 地图翻页额外等待时间，用于覆盖较长的节点动画。
MAP_PAGE_TRANSITION_DELAY = 0.2000


# ── 章节导航入口 ─────────────────────────────────────────────────────────────


def ensure_chapter(ctx: ContextHandle, *, chapter: int, map_id: int) -> None:
    """确保出征页选中目标的章节与地图节点。

    顺序与原有普通出征导航一致：

    1. 确保停在出征标签；
    2. 按侧栏槽位 OCR 循环选章，连续命中两次才算到达；
    3. 按地图标题 OCR 逐跳翻页选节，卡住或识别失败达到上限时重启本轮。

    Args:
        ctx: 提供设备服务与截图事实的 dispatch 上下文句柄。
        chapter: 目标章节编号，范围为 1 到 TOTAL_CHAPTERS。
        map_id: 目标地图节点编号，范围由当前章的地图数量决定。

    Raises:
        ValueError: 章节编号越界，或当前章不在已知地图数据中。
        NavigationError: 选章连续无进展或超过尝试上限。
        RuntimeError: 选节超过尝试上限，或任务没有绑定 OCR 引擎。
    """
    if not 1 <= chapter <= constants.TOTAL_CHAPTERS:
        raise ValueError(f'章节编号必须为 1-{constants.TOTAL_CHAPTERS}，收到: {chapter}')

    _ensure_sortie_tab(ctx)
    if not _select_target_chapter(ctx, chapter):
        raise NavigationError(f'无法导航到第 {chapter} 章')
    _select_target_map(ctx, map_id)


# ── 出征标签 ─────────────────────────────────────────────────────────────────


def _ensure_sortie_tab(ctx: ContextHandle) -> None:
    """确保停在出征标签：已经在就不点，不在则点一次并确认。

    Args:
        ctx: 提供设备服务与截图事实的 dispatch 上下文句柄。

    Raises:
        NavigationError: 点击标签后仍未激活。
    """
    if check_sortie_page(ctx, attempts=1, interval_seconds=0.2):
        return
    SortiePage(ctx).go_to(SortieTab.SORTIE)
    if not check_sortie_page(ctx):
        raise NavigationError('章节导航失败：未切到出征标签')


# ── 选章 ─────────────────────────────────────────────────────────────────────


def _select_target_chapter(ctx: ContextHandle, target: int) -> bool:
    """循环选章，到达目标章返回 True。

    Args:
        ctx: 提供设备服务与截图事实的 dispatch 上下文句柄。
        target: 目标章节编号。

    Returns:
        连续确认到达目标章时为 True；连续无进展或超过尝试上限时为 False。
    """
    page = BattlePage(ctx)
    confirm_hits = 0
    previous_current: int | None = None
    no_progress = 0

    for attempt in range(CHAPTER_NAV_MAX_ATTEMPTS):
        slots, current = recognition.read_chapter_state(ctx)
        slot_state = [
            slot.chapter if slot.chapter is not None else slot.text or '---' for slot in slots
        ]
        if current is None:
            _log.warning('[UI] 章节导航：中间章节槽位识别失败（第 {} 次尝试）', attempt + 1)
            time.sleep(MAP_NAV_SETTLE_DELAY)
            continue

        if previous_current == current:
            no_progress += 1
        else:
            no_progress = 0
        previous_current = current
        if no_progress >= CHAPTER_NO_PROGRESS_LIMIT:
            _log.warning('[UI] 章节导航：连续无进展，槽位={}', slot_state)
            return False

        if current == target:
            confirm_hits += 1
            _log.info(
                '[UI] 章节导航：命中目标第 {} 章，确认 {}/{}, 槽位={}',
                target,
                confirm_hits,
                CHAPTER_CONFIRMATION_COUNT,
                slot_state,
            )
            if confirm_hits >= CHAPTER_CONFIRMATION_COUNT:
                _log.info('[UI] 章节导航：已到达第 {} 章', target)
                return True
            time.sleep(MAP_NAV_SETTLE_DELAY)
            continue

        confirm_hits = 0
        index = _calculate_chapter_slot(current, target, slots)
        if index is None:
            _log.warning(
                '[UI] 章节导航：目标第 {} 章没有可用槽位（当前={}, 槽位={}）',
                target,
                current,
                slot_state,
            )
            time.sleep(MAP_NAV_SETTLE_DELAY)
            continue

        page.click_chapter_slot(index)
        time.sleep(MAP_NAV_SETTLE_DELAY)

    _log.warning(
        '[UI] 章节导航：超过最大尝试次数（{}），目标第 {} 章',
        CHAPTER_NAV_MAX_ATTEMPTS,
        target,
    )
    return False


def _calculate_chapter_slot(
    current: int,
    target: int,
    slots: Sequence[ChapterSlot],
) -> int | None:
    """根据可见章节槽位计算下一次点击位置。

    先找视图内已经是目标章的槽位；否则按步长（相邻 1 章、跨 2 章）向目标方向移动。
    算出的槽位必须回验其识别值等于预期章号，避免按没识别出来的槽位盲点。

    Args:
        current: 当前章节编号。
        target: 目标章节编号。
        slots: 当前画面可见的章节槽位识别结果。

    Returns:
        下一次应点击的槽位索引；没有安全点击位置时返回 None。
    """
    for slot in slots:
        if slot.chapter == target:
            return slot.index

    delta = target - current
    if delta == 0:
        return None

    step = CHAPTER_DOUBLE_STEP if abs(delta) >= CHAPTER_DOUBLE_STEP else CHAPTER_SINGLE_STEP
    direction = 1 if delta > 0 else -1
    index = recognition.CHAPTER_SLOT_CENTER_INDEX + direction * step
    if not 0 <= index < len(slots):
        return None

    expected = current + direction * step
    return index if slots[index].chapter == expected else None


# ── 选节 ─────────────────────────────────────────────────────────────────────


def _select_target_map(ctx: ContextHandle, map_num: int) -> None:
    """逐跳翻页选节，到达目标节后返回。

    Args:
        ctx: 提供设备服务与截图事实的 dispatch 上下文句柄。
        map_num: 目标地图节点编号。

    Raises:
        ValueError: 当前章未知，或目标节超出当前章范围。
        RuntimeError: 读不到当前地图标题，或翻页超过尝试上限。
    """
    target = int(map_num)
    info_probe = recognition.read_map_identity(ctx)
    if info_probe is None:
        raise RuntimeError('无法识别当前地图标题，不能校验地图编号')
    current_max = constants.CHAPTER_MAP_COUNTS.get(int(info_probe.chapter))
    if current_max is None:
        raise ValueError(f'当前章节 {info_probe.chapter} 不在已知地图数据中')
    if not 1 <= target <= current_max:
        raise ValueError(
            f'地图编号 map_num={target} 超出范围 [1, {current_max}]（当前章识别失败时请先选章）',
        )

    page = BattlePage(ctx)
    confirm = 0
    for attempt in range(CHAPTER_NAV_MAX_ATTEMPTS):
        current, stable = _read_stable_map_number(ctx)
        if current is None:
            _log.warning(
                '[UI] 地图节点导航：OCR 识别失败（第 {}/{} 次尝试）',
                attempt + 1,
                CHAPTER_NAV_MAX_ATTEMPTS,
            )
            continue

        if current == target:
            confirm += 1
            _log.info(
                '[UI] 地图节点导航：命中目标 {}-{}，确认 {}/{}',
                current,
                target,
                confirm,
                MAP_CONFIRMATION_COUNT,
            )
            if confirm >= MAP_CONFIRMATION_COUNT:
                _log.info(
                    '[UI] 地图节点导航：已到达当前章第 {} 节（地图编号 {}）',
                    target,
                    target,
                )
                return
            time.sleep(MAP_NAV_SETTLE_DELAY)
            continue

        confirm = 0
        if not stable:
            time.sleep(MAP_NAV_SETTLE_DELAY)
            continue

        settled = _advance_map_node(ctx, page, current, target)
        if settled is None:
            continue

    raise RuntimeError(
        f'地图节点导航超过最大尝试次数 {CHAPTER_NAV_MAX_ATTEMPTS}，目标节 {target} 未到达',
    )


def _advance_map_node(
    ctx: ContextHandle,
    page: BattlePage,
    current: int,
    target: int,
) -> int | None:
    """按节号差逐跳翻页到目标附近。

    Args:
        ctx: 提供设备服务与截图事实的 dispatch 上下文句柄。
        page: 普通出征页面单击控制器。
        current: 本轮开始时的当前节号。
        target: 目标节号。

    Returns:
        本轮结束时的当前节号；卡住或识别失败达到上限时返回 None，由调用方重启本轮。
    """
    delta = target - current
    direction = 1 if delta > 0 else -1
    remaining = abs(delta)
    stuck = 0
    misses = 0
    steps = 0

    _log.info('[UI] 地图节点导航：当前 {} -> 目标 {}（delta={:+d}）', current, target, delta)

    while remaining > 0 and stuck < MAP_MAX_STUCK and misses < MAP_NAVIGATION_MISS_LIMIT:
        if direction == 1:
            page.click_map_next()
            action = '下一节'
        else:
            page.click_map_prev()
            action = '上一节'
        steps += 1
        remaining -= 1
        _log.info('[UI] 地图节点导航：{}（剩余 {}，第 {} 跳）', action, remaining, steps)
        time.sleep(MAP_NAV_SETTLE_DELAY + MAP_PAGE_TRANSITION_DELAY)

        quick = _read_map_number(ctx)
        if quick is None:
            misses += 1
            continue
        misses = 0
        if (direction == 1 and quick <= current) or (direction == -1 and quick >= current):
            stuck = 1 if (quick == current and stuck == 0) else stuck + 1
            _log.warning(
                '[UI] 地图节点导航：翻页后仍是第{}节（cur={}, stuck={}/{}）',
                quick,
                current,
                stuck,
                MAP_MAX_STUCK,
            )
            continue
        stuck = 0
        current = quick
        remaining = abs(target - current)

    if stuck >= MAP_MAX_STUCK or misses >= MAP_NAVIGATION_MISS_LIMIT:
        _log.warning(
            '[UI] 地图节点导航：卡住或识别失败超限（stuck={}, misses={}），重启本轮',
            stuck,
            misses,
        )
        return None
    return current


def _read_map_number(ctx: ContextHandle) -> int | None:
    """读一次当前地图节点编号。

    Args:
        ctx: 提供设备服务与截图事实的 dispatch 上下文句柄。

    Returns:
        当前节点编号；标题读不到或无法解析时为 None。
    """
    identity = recognition.read_map_identity(ctx)
    return identity.map_num if identity is not None else None


def _read_stable_map_number(ctx: ContextHandle) -> tuple[int | None, bool]:
    """多次采样读取当前地图编号，并判断采样是否稳定。

    Args:
        ctx: 提供设备服务与截图事实的 dispatch 上下文句柄。

    Returns:
        当前地图编号与稳定标记；一次都没读到时为 (None, False)。
    """
    map_numbers: list[int] = []
    for sample_index in range(MAP_READ_SAMPLE_COUNT):
        number = _read_map_number(ctx)
        if number is not None:
            map_numbers.append(number)
        if sample_index < MAP_READ_SAMPLE_COUNT - 1:
            time.sleep(MAP_READ_SAMPLE_DELAY)
    return _judge_stable_map_number(map_numbers)


def _judge_stable_map_number(map_numbers: Sequence[int]) -> tuple[int | None, bool]:
    """判断多次采样的地图编号是否稳定。

    末两次相同，或采满且全部相同即为稳定；否则取众数并标记为抖动。

    Args:
        map_numbers: 本轮采样到的地图编号。

    Returns:
        当前地图编号与稳定标记；没有采样结果时为 (None, False)。
    """
    if not map_numbers:
        return None, False
    if len(map_numbers) >= MAP_READ_STABLE_COUNT and map_numbers[-1] == map_numbers[-2]:
        return map_numbers[-1], True
    if len(map_numbers) == MAP_READ_SAMPLE_COUNT and len(set(map_numbers)) == 1:
        return map_numbers[0], True

    candidate = max(set(map_numbers), key=map_numbers.count)
    _log.warning('[UI] 地图节点导航：OCR 抖动 {}，本轮不点击', map_numbers)
    return candidate, False


__all__ = ['ensure_chapter']
