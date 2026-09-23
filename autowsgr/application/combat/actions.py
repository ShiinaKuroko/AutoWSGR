"""战斗动作子系统。

本模块只执行战斗页面上的物理动作。坐标来自 UI 校准资源，识别和结果采集
由 ``recognition`` 子系统负责，战斗阶段编排由 ``handlers`` 负责。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.common.calibration.coordinates import point
from autowsgr.common.system import get_logger
from autowsgr.common.vision._resources import TemplateKey, Templates
from autowsgr.common.vision._template_matcher import ImageChecker


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.device import AndroidController
    from autowsgr.common.types import FightCondition, Formation


_log = get_logger('combat')


def _combat_point(key: str) -> tuple[float, float]:
    """读取战斗页面的校准坐标。"""
    return point('combat', key)


# ═══════════════════════════════════════════════════════════════════════════════
# 操作函数
# ═══════════════════════════════════════════════════════════════════════════════


def click_retreat(device: AndroidController) -> None:
    """点击撤退按钮（索敌成功界面）。"""
    device.click(*_combat_point('retreat'))
    time.sleep(0.2)


def click_enter_fight(device: AndroidController) -> None:
    """点击进入战斗（索敌成功界面）。"""
    time.sleep(0.5)
    device.click(*_combat_point('enter_fight'))
    time.sleep(0.2)


def click_formation(device: AndroidController, formation: Formation) -> None:
    """选择阵型。

    Parameters
    ----------
    device:
        设备控制器。
    formation:
        目标阵型。
    """
    _log.debug('[Action] 选择阵型: {} ({})', formation.name, formation.value)
    x, y = formation.relative_position
    device.click(x, y)
    time.sleep(2.0)


def click_fight_condition(device: AndroidController, condition: FightCondition) -> None:
    """选择战况。
    Parameters
    ----------
    device:
        设备控制器。
    condition:
        目标战况。
    """
    x, y = condition.relative_click_position

    # 选择战况后，舰队会在地图上移动，不能添加延迟，否则会出现识别不到下一个点的问题
    device.click(x, y, delay=False)


def click_night_battle(device: AndroidController, pursue: bool) -> None:
    """夜战选择。

    Parameters
    ----------
    device:
        设备控制器。
    pursue:
        ``True`` = 追击（进入夜战），``False`` = 撤退。
    """
    _log.debug('[Action] 夜战选择: {}', '追击' if pursue else '撤退')
    if pursue:
        device.click(*_combat_point('night_yes'))
    else:
        device.click(*_combat_point('night_no'))


def click_proceed(device: AndroidController, go_forward: bool) -> None:
    """继续前进 / 回港选择。

    Parameters
    ----------
    device:
        设备控制器。
    go_forward:
        ``True`` = 前进，``False`` = 回港。
    """
    _log.debug('[Action] 继续前进: {}', '前进' if go_forward else '回港')
    if go_forward:
        device.click(*_combat_point('proceed_yes'))
    else:
        device.click(*_combat_point('proceed_no'))


def click_result(device: AndroidController) -> None:
    """点击战果页面继续。"""
    device.click(*_combat_point('click_result'))


def click_speed_up(device: AndroidController, *, battle_mode: bool = False) -> None:
    """点击加速（移动中或战役中）。

    Parameters
    ----------
    device:
        设备控制器。
    battle_mode:
        ``True`` 使用战役加速坐标，``False`` 使用常规战坐标。
    """
    coords = _combat_point('speed_up_battle' if battle_mode else 'speed_up_normal')

    # 由于加速过快可能导致卡顿, 增加极短延迟以确保点击生效
    time.sleep(0.05)
    device.click(*coords, delay=False)


def click_skip_missile_animation(device: AndroidController) -> None:
    """跳过导弹支援动画。"""

    # 快速点击不需要增加操作后的 delay
    device.click(*_combat_point('speed_up_battle'), delay=False)


def click_image(
    device: AndroidController,
    template_key: TemplateKey | str,
    timeout: float,
) -> bool:
    """等待模板出现并点击其中心。"""
    if isinstance(template_key, str):
        template_key = TemplateKey(template_key)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        detail = ImageChecker.find_any(
            device.screenshot(),
            template_key.templates,
            confidence=0.8,
        )
        if detail is not None:
            device.click(*detail.center)
            return True
        time.sleep(0.3)
    return False


def dismiss_resource_confirm(device: AndroidController, screen: np.ndarray) -> None:
    """在当前截图中发现资源确认弹窗时点击确认。"""
    detail = ImageChecker.find_any(
        screen,
        [Templates.Confirm.CONFIRM_1],
        confidence=0.75,
    )
    if detail is None:
        return
    time.sleep(0.25)
    device.click(*detail.center, delay=False)
    _log.info(
        "[Combat] 点掉资源确认弹窗: '{}' ({:.4f}, {:.4f})",
        detail.template_name,
        *detail.center,
    )
    time.sleep(1)
    device.click(*_combat_point('speed_up_battle'), delay=False)


__all__ = [
    'click_enter_fight',
    'click_fight_condition',
    'click_formation',
    'click_image',
    'click_night_battle',
    'click_proceed',
    'click_result',
    'click_retreat',
    'click_skip_missile_animation',
    'click_speed_up',
    'dismiss_resource_confirm',
]
