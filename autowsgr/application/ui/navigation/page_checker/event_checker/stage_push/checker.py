"""模块功能：编排普通推图活动的页面识别入口。

上层调用：
- application.ui.navigation：确认首页活动入口、活动地图状态和出征准备前置页。

下层依赖：
- event.calibration：校验活动玩法并加载本期活动数据。
- event_checker.stage_push.constants：提供本活动标识。
- event_checker.stage_push.recognition：读取页面识别事实与难度结论。

边界：只编排识别并组装页面事实，不执行点击、不计算路由、不上报识别错误。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.page_checker import calibration
from autowsgr.application.ui.navigation.page_checker.event_checker.stage_push import (
    constants,
    recognition,
)
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from autowsgr.application.ui.navigation.page_checker.event_checker.stage_push.recognition import (
        EventMode,
    )
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 活动页面事实模型 ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class EventMapState:
    """活动地图页面的事实与结论。

    Attributes:
        on_clean_map: 当前是否为没有节点浮窗的干净地图页。
        button_mode: 模式按钮显示的模式，即点击后要切换到的难度；没有按钮时为 None。
        title_mode: 地图标题对应的难度；没有读到标题时为 None。
        current_mode: 由按钮和标题推出的当前难度；浮窗态、矛盾或读不到时为 None。
    """

    on_clean_map: bool
    button_mode: EventMode | None
    title_mode: EventMode | None
    current_mode: EventMode | None


@dataclass(frozen=True, slots=True)
class EventStage:
    """活动章节的执行参数。

    Attributes:
        difficulty: 章节难度。
        node: 章节在地图上的落点序号。
    """

    difficulty: recognition.EventMode
    node: int


# ── 章节解析 ────────────────────────────────────────────────────────────────

# 地图上的落点数量；普通与困难共用同一组落点。
_NODE_COUNT = 6


def parse_stage(stage: str) -> EventStage:
    """把任务里的章节标识解析成执行参数。

    支持任务契约的 `EX1`-`EX12`，以及旧控制器的 `E1`-`E6` / `H1`-`H6` 写法。

    Args:
        stage: 章节标识。

    Returns:
        章节的执行参数：难度与落点序号。

    Raises:
        ValueError: 标识格式非法或超出范围。
    """
    number = _stage_number(stage)
    difficulty = (
        recognition.EventMode.NORMAL if number <= _NODE_COUNT else recognition.EventMode.HARD
    )
    return EventStage(difficulty=difficulty, node=(number - 1) % _NODE_COUNT + 1)


def _stage_number(stage: str) -> int:
    """把章节标识换算成跨难度的全局编号（1-12）。

    Raises:
        ValueError: 标识格式非法或超出范围。
    """
    text = stage.strip().upper()
    legacy = len(text) == 2 and text[0] in ('E', 'H')
    if text.startswith('EX'):
        digits = text[2:]
    elif legacy:
        digits = text[1:]
    else:
        raise ValueError(f'无效的章节标识: {stage!r}')
    if not digits.isdigit():
        raise ValueError(f'无效的章节标识: {stage!r}')

    number = int(digits)
    if legacy:
        if not 1 <= number <= _NODE_COUNT:
            raise ValueError(f'章节标识超出范围: {stage!r}')
        if text[0] == 'H':
            number += _NODE_COUNT
    elif not 1 <= number <= _NODE_COUNT * 2:
        raise ValueError(f'章节标识超出范围: {stage!r}')
    return number


# ── 识别入口 ────────────────────────────────────────────────────────────────


def check_event_map_page(ctx: ContextHandle, *, event_type: str) -> bool:
    """确认当前是否在活动地图页。

    判断标准：地图标题区域识别到本期地图名。章节浮窗态由浮窗入口单独确认。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        event_type: 活动玩法标识。

    Returns:
        读到地图标题时为真。

    Raises:
        ValueError: 活动玩法标识与当前 checker 不一致。
    """
    calibration.require_activity(event_type, constants.ACTIVITY)
    data = calibration.load_activity_data(constants.ACTIVITY, constants.PERIOD)
    return recognition.is_map_title_present(ctx, data)


def check_event_entry(ctx: ContextHandle, *, event_type: str) -> bool:
    """确认首页活动入口卡片是否可见。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        event_type: 活动玩法标识，用于确认调用方选对了 checker。

    Returns:
        入口模板命中时为真；读不到时为假，由调用方决定如何处理。
    """
    calibration.require_activity(event_type, constants.ACTIVITY)
    return recognition.is_event_entry_visible(ctx)


def read_event_map_state(ctx: ContextHandle, *, event_type: str) -> EventMapState:
    """读取活动地图页面的难度事实并给出当前难度。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        event_type: 活动玩法标识，用于确认调用方选对了 checker。

    Returns:
        活动地图页面事实；浮窗态、矛盾或读不到时结论为空。
    """
    calibration.require_activity(event_type, constants.ACTIVITY)
    data = calibration.load_activity_data(constants.ACTIVITY, constants.PERIOD)

    # 1. 分别读取模式按钮和地图标题，两者都是当前难度的独立证据。
    button_mode = recognition.read_mode_button(ctx)
    title_mode = recognition.read_map_title(ctx, data)

    # 2. 浮窗会压暗整页并让模式按钮模板失效，因此浮窗态不下难度结论。
    on_clean_map = not recognition.is_sortie_overlay_open(ctx, data)

    state = EventMapState(
        on_clean_map=on_clean_map,
        button_mode=button_mode,
        title_mode=title_mode,
        current_mode=recognition.calculate_current_mode(button_mode, title_mode)
        if on_clean_map
        else None,
    )
    _log.debug(
        '[UI] 活动地图 → 读状态：on_clean_map={!r}，button_mode={!r}，title_mode={!r}，current_mode={!r}',
        state.on_clean_map,
        state.button_mode,
        state.title_mode,
        state.current_mode,
    )
    return state


def check_event_sortie_prepare(ctx: ContextHandle, *, event_type: str, stage: str) -> bool:
    """确认节点浮窗已打开且指向目标章节。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        event_type: 活动玩法标识，用于确认调用方选对了 checker。
        stage: 目标章节标识，例如 EX7。

    Returns:
        浮窗模板命中且标题指向目标章节时为真。

    Raises:
        ValueError: 本期活动数据里没有该章节。
    """
    calibration.require_activity(event_type, constants.ACTIVITY)
    data = calibration.load_activity_data(constants.ACTIVITY, constants.PERIOD)
    if stage not in data['stages']:
        raise ValueError(f'本期活动没有该章节: {stage!r}')

    # 1. 先等节点浮窗出现，浮窗没有出现时不需要继续判定标题。
    if not recognition.wait_sortie_overlay(ctx):
        return False

    # 2. 再用关卡标题确认进入的是目标章节。
    title_texts = recognition.read_stage_title_texts(ctx, data)
    matched = recognition.is_stage_title_matched(title_texts, stage, data)
    _log.debug('[UI] 出征准备前置页 → 校验章节：stage={!r}，matched={!r}', stage, matched)
    return matched


def read_sortie_prepare_center(
    ctx: ContextHandle,
    *,
    event_type: str,
) -> tuple[float, float] | None:
    """读取节点浮窗内"确认出征"按钮的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        event_type: 活动玩法标识，用于确认调用方选对了 checker。

    Returns:
        按钮模板命中时的归一化中心；未命中时为 None。
    """
    calibration.require_activity(event_type, constants.ACTIVITY)
    return recognition.read_sortie_prepare_center(ctx)
