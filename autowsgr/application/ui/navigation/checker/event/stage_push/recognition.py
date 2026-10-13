"""模块功能：把画面解释为普通推图活动的页面事实。

上层调用：
- application.ui.navigation.checker.event.stage_push.checker：读取页面识别事实与难度结论。

下层依赖：
- common.vision：提供前识别入口和识别结果模型。
- event.calibration：加载本活动的模板。
- event.stage_push.constants：提供活动标识、识别坐标与模板文件名。

边界：只把画面读成事实并解析识别文本；本期活动的识别期望文本留在本模块，不读文件、不组装页面结论。
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.checker import calibration
from autowsgr.application.ui.navigation.checker.event.stage_push import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import expect_ocr, expect_template, expect_template_center


if TYPE_CHECKING:
    from collections.abc import Sequence

    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui')


# ── 活动事实模型 ────────────────────────────────────────────────────────────────────


class EventMode(StrEnum):
    """活动地图难度。"""

    NORMAL = 'normal'
    HARD = 'hard'


# ── 本期活动识别期望 ────────────────────────────────────────────────────────────────

# 地图名与关卡名，换期只改这一段。困难模式的标题在本名后追加"困难"二字；
# 括号形态不稳定，因此不参与比对，只判"标题 + 困难"。
_MAP_NAME = '最强之舟'
_STAGE_NAMES = {
    1: '天降火雨',
    2: '鹰群出击',
    3: '追逐跳跃',
    4: '火力全开',
    5: '四面合围',
    6: '海空鏖战',
}


# ── 识别判定参数 ────────────────────────────────────────────────────────────────────

# 模板匹配命中阈值。
_TEMPLATE_CONFIDENCE = 0.85
# 只读探测只取当前一帧，不等待目标出现。
_PROBE_ATTEMPTS = 1
# 困难模式的固定标记；实测标题括号有全角、半角和丢失三种形态，因此只判这两个字。
_HARD_MARKER = '困难'
# 标题归一化时丢弃的装饰字符，保留数字、字母和汉字。
_TITLE_DECORATION = re.compile(r'[^0-9a-zA-Z一-鿿]+')
# 归一化标题里的关卡编号形式，大小写不敏感。
_STAGE_TITLE_PATTERN = re.compile(r'ex(\d+)')


# ── 识别文本解析 ────────────────────────────────────────────────────────────────────


def _normalize_title(text: str) -> str:
    """去掉标题里的装饰字符并统一小写。"""
    return _TITLE_DECORATION.sub('', text).lower()


def _parse_title_stage_number(title: str) -> int | None:
    """从归一化标题里取出关卡编号。"""
    matched = _STAGE_TITLE_PATTERN.match(title)
    return int(matched.group(1)) if matched else None


def _calculate_mode_from_title(title_texts: Sequence[str]) -> EventMode | None:
    """由地图标题文本判断难度。"""
    # 困难标记是困难模式独有的文字，先判它，避免名称前缀被普通地图名抢先命中。
    if any(_HARD_MARKER in text for text in title_texts):
        return EventMode.HARD
    if any(_MAP_NAME in text for text in title_texts):
        return EventMode.NORMAL
    return None


# ── 页面事实读取与判断 ─────────────────────────────────────────────────────────────────


def read_event_entry(ctx: ContextHandle) -> bool:
    """判断首页活动入口卡片是否可见。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        入口模板命中时为真。
    """
    result = expect_template(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.HOME_ENTRY_TEMPLATE,
            name='event_home_entry',
        ),
        roi=constants.HOME_ENTRY_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
    )
    _log.debug('[UI] 活动识别 → 查活动入口：visible={!r}', result.satisfied)
    return result.satisfied


def read_mode_button(ctx: ContextHandle) -> EventMode | None:
    """读取模式按钮显示的模式。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        模式按钮指向的难度；两张模板都没命中时为 None。
    """
    normal_template = calibration.load_module_template(
        constants.TEMPLATE_NAMESPACE,
        constants.MODE_NORMAL_TEMPLATE,
        name='event_mode_normal',
    )
    hard_template = calibration.load_module_template(
        constants.TEMPLATE_NAMESPACE,
        constants.MODE_HARD_TEMPLATE,
        name='event_mode_hard',
    )
    result = expect_template(
        ctx,
        template=(normal_template, hard_template),
        roi=constants.MODE_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
        attempts=_PROBE_ATTEMPTS,
    )
    normal_match, hard_match = result.observation
    button_mode = None
    if normal_match.matched:
        button_mode = EventMode.NORMAL
    elif hard_match.matched:
        button_mode = EventMode.HARD
    _log.debug('[UI] 活动识别 → 读模式按钮：button_mode={!r}', button_mode)
    return button_mode


def read_map_title(
    ctx: ContextHandle,
    *,
    attempts: int = _PROBE_ATTEMPTS,
    interval_seconds: float = 0.5,
) -> EventMode | None:
    """读取地图标题并判断难度。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        地图标题对应的难度；读不到时为 None。
    """
    result = expect_ocr(
        ctx,
        expect=(_MAP_NAME, f'{_MAP_NAME}（困难）'),
        roi=constants.MAP_NAME_ROI,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )
    title_texts = [detection.recognized_text for detection in result.observation]
    title_mode = _calculate_mode_from_title(title_texts)
    _log.debug('[UI] 活动识别 → 读地图标题：title_mode={!r}，texts={!r}', title_mode, title_texts)
    return title_mode


def read_stage_title_texts(ctx: ContextHandle) -> list[str]:
    """读取关卡标题文本。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        关卡标题的识别文本。
    """
    # 标题由"EX+编号+名称"组成，无法用固定文本等待，因此用候选集合触发一次读取后自行判定。
    result = expect_ocr(
        ctx,
        expect=tuple(_STAGE_NAMES.values()),
        roi=constants.STAGE_TITLE_ROI,
        attempts=_PROBE_ATTEMPTS,
    )
    title_texts = [detection.recognized_text for detection in result.observation]
    _log.debug('[UI] 活动识别 → 读关卡标题：texts={!r}', title_texts)
    return title_texts


def wait_sortie_overlay(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """确认节点浮窗是否在画面上。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        absent: 期望浮窗消失时为真，默认期望它出现。
        attempts: 识别次数，默认只探测当前一帧。
        interval_seconds: 两次识别之间的等待秒数。

    Returns:
        断言满足时为真。
    """
    result = expect_template(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.SORTIE_PREPARE_TEMPLATE,
            name='event_sortie_prepare',
        ),
        roi=constants.SORTIE_PREPARE_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
        absent=absent,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )
    return result.satisfied


def read_mode_button_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取模式按钮的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        模式按钮模板命中时的归一化中心；未命中时为 None。
    """
    center = expect_template_center(
        ctx,
        template=(
            calibration.load_module_template(
                constants.TEMPLATE_NAMESPACE,
                constants.MODE_NORMAL_TEMPLATE,
                name='event_mode_normal',
            ),
            calibration.load_module_template(
                constants.TEMPLATE_NAMESPACE,
                constants.MODE_HARD_TEMPLATE,
                name='event_mode_hard',
            ),
        ),
        roi=constants.MODE_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
        attempts=_PROBE_ATTEMPTS,
    )
    _log.debug('[UI] 活动识别 → 读模式按钮中心：center={!r}', center)
    return center


def read_sortie_prepare_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取节点浮窗内"确认出征"按钮的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        按钮模板命中时的归一化中心；未命中时为 None。
    """
    center = expect_template_center(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.SORTIE_PREPARE_TEMPLATE,
            name='event_sortie_prepare',
        ),
        roi=constants.SORTIE_PREPARE_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
        attempts=_PROBE_ATTEMPTS,
    )
    _log.debug('[UI] 活动识别 → 读确认出征中心：center={!r}', center)
    return center


def read_sortie_overlay(ctx: ContextHandle) -> bool:
    """判断节点浮窗当前是否已经打开。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        浮窗已经打开时为真。
    """
    result = expect_template(
        ctx,
        template=calibration.load_module_template(
            constants.TEMPLATE_NAMESPACE,
            constants.SORTIE_PREPARE_TEMPLATE,
            name='event_sortie_prepare',
        ),
        roi=constants.SORTIE_PREPARE_ROI,
        confidence=_TEMPLATE_CONFIDENCE,
        attempts=_PROBE_ATTEMPTS,
    )
    # 浮窗打开时关卡标题才出现，用标题文字补强模板判据。
    overlay_open = result.satisfied or bool(read_stage_title_texts(ctx))
    _log.debug('[UI] 活动识别 → 判节点浮窗：overlay_open={!r}', overlay_open)
    return overlay_open


def is_stage_title_matched(title_texts: Sequence[str], *, node: int, hard: bool) -> bool:
    """判断关卡标题是否指向目标章节。

    Args:
        title_texts: 关卡标题的识别文本。
        node: 目标章节在地图上的落点序号，1 到 6。
        hard: 目标章节是否属于困难模式。

    Returns:
        标题命中目标章节时为真：模式一致，且编号或名称任一命中。
    """
    stage_name = _STAGE_NAMES[node]
    stage_number = node + (len(_STAGE_NAMES) if hard else 0)
    for text in title_texts:
        normalized = _normalize_title(text)
        # 普通与困难共用同一批章节名，只有 "困难" 二字能区分两者：模式不符直接排除，
        # 否则同名困难章节会被普通章节的判据抢先命中。
        if (_HARD_MARKER in normalized) != hard:
            continue
        # 关卡编号和章节名称任一命中即算匹配，兼容标题编号被 OCR 丢字的情况。
        if _parse_title_stage_number(normalized) == stage_number:
            return True
        if stage_name in normalized:
            return True
    return False


def calculate_current_mode(
    button_mode: EventMode | None,
    title_mode: EventMode | None,
) -> EventMode | None:
    """由模式按钮和地图标题推出当前难度。

    Args:
        button_mode: 模式按钮读出的难度。
        title_mode: 地图标题读出的难度。

    Returns:
        两者一致指向的难度；证据矛盾或都读不到时为 None。
    """
    # 1. 按钮和标题互为反向证据时，两者一致指向同一种当前难度。
    if button_mode is EventMode.NORMAL and title_mode is EventMode.HARD:
        return EventMode.HARD
    if button_mode is EventMode.HARD and title_mode is EventMode.NORMAL:
        return EventMode.NORMAL

    # 2. 没有按钮说明困难难度尚未开放，此时只可能是普通地图。
    if button_mode is None and title_mode is EventMode.NORMAL:
        return EventMode.NORMAL

    # 3. 其余组合是矛盾或读不到，结论交给调用方判断。
    return None
