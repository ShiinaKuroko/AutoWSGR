"""战斗识别的应用层适配。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.combat.recognizer import CombatRecognitionTimeoutError
from autowsgr.application.ui.pages.battle_preparation.blood import classify_blood
from autowsgr.common.system import get_logger
from autowsgr.common.types import ShipDamageState
from autowsgr.common.vision import ImageChecker, PixelChecker
from autowsgr.common.vision.combat import (
    RESULT_BLOOD_BAR_PROBE,
    SHIP_DROP_PAGE_SIGNATURE,
    ShipDropResult,
    detect_mvp,
    get_enemy_formation,
    get_enemy_info,
    get_ship_drop,
    image_exist,
    recognize_enemy_formation,
    recognize_enemy_ships,
    recognize_ship_drop,
)
from autowsgr.common.vision.resources.keys import RESULT_GRADE_KEYS


if TYPE_CHECKING:
    from autowsgr.common.device import AndroidController


_log = get_logger('combat.recognition')


def detect_result_grade(device: AndroidController) -> str:
    """从战果截图采集业务评级。"""
    for _ in range(5):
        screen = device.screenshot()
        for grade, key in RESULT_GRADE_KEYS.items():
            if ImageChecker.find_any(screen, key.templates, confidence=0.8) is not None:
                return grade
        time.sleep(0.25)
    raise CombatRecognitionTimeoutError('战果等级识别超时: 5 次尝试未识别到有效等级')


def detect_ship_stats(
    device: AndroidController,
    pre_battle_stats: list[ShipDamageState],
) -> list[ShipDamageState]:
    """把结算页血条像素结果转换为业务血量状态。"""
    screen = device.screenshot()
    result: list[ShipDamageState] = [ShipDamageState.NORMAL] * 6
    for slot, (x, y) in RESULT_BLOOD_BAR_PROBE.items():
        if pre_battle_stats[slot] == ShipDamageState.NO_SHIP:
            result[slot] = ShipDamageState.NO_SHIP
        else:
            result[slot] = classify_blood(PixelChecker.get_pixel(screen, x, y))
    _log.info('[Combat] 结算页血量检测: {}', [state.name for state in result])
    return result


__all__ = [
    'SHIP_DROP_PAGE_SIGNATURE',
    'ShipDropResult',
    'detect_mvp',
    'detect_result_grade',
    'detect_ship_stats',
    'get_enemy_formation',
    'get_enemy_info',
    'get_ship_drop',
    'image_exist',
    'recognize_enemy_formation',
    'recognize_enemy_ships',
    'recognize_ship_drop',
]
