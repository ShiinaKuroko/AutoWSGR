"""Reusable combat application capabilities.

Business runners choose the plan and interpret results; this package performs
the common combat loop and device/vision actions.
"""

from autowsgr.application.combat.actions import (
    click_enter_fight,
    click_fight_condition,
    click_formation,
    click_image,
    click_night_battle,
    click_proceed,
    click_result,
    click_retreat,
    click_skip_missile_animation,
)
from autowsgr.application.combat.engine import (
    CombatEngine,
    CombatPhase,
)
from autowsgr.application.combat.node_tracker import MapNodeData, NodeTracker
from autowsgr.application.combat.recognition import (
    SHIP_DROP_PAGE_SIGNATURE,
    ShipDropResult,
    detect_mvp,
    detect_result_grade,
    detect_ship_stats,
    get_enemy_formation,
    get_enemy_info,
    get_ship_drop,
    image_exist,
    recognize_enemy_formation,
    recognize_enemy_ships,
    recognize_ship_drop,
)
from autowsgr.application.combat.recognizer import (
    CombatRecognitionTimeoutError,
    CombatRecognizer,
    CombatStopRequestedError,
)


__all__ = [
    'SHIP_DROP_PAGE_SIGNATURE',
    'CombatEngine',
    'CombatPhase',
    'CombatRecognitionTimeoutError',
    'CombatRecognizer',
    'CombatStopRequestedError',
    'MapNodeData',
    'NodeTracker',
    'ShipDropResult',
    'click_enter_fight',
    'click_fight_condition',
    'click_formation',
    'click_image',
    'click_night_battle',
    'click_proceed',
    'click_result',
    'click_retreat',
    'click_skip_missile_animation',
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
