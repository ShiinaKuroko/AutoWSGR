"""演习页面的坐标和颜色校准值。"""

from __future__ import annotations

from autowsgr.application.vision.calibration._loader import color, tolerance
from autowsgr.application.vision.calibration._loader import point, points


RIVAL_POSITIONS = points('exercise', 'rival_positions')
CLICK_CHALLENGE = point('exercise', 'click_challenge')
EXERCISE_CHALLENGE_COLOR = color('exercise', 'challenge_blue')
EXERCISE_CHALLENGE_TOLERANCE = tolerance('exercise', 'challenge_blue')
EXERCISE_ARROW_GRAY = color('exercise', 'arrow_gray')
EXERCISE_ARROW_TOLERANCE = tolerance('exercise', 'arrow_gray')
EXERCISE_ARROW_UP_PROBE = point('exercise', 'arrow_up_probe')
EXERCISE_ARROW_DOWN_PROBE = point('exercise', 'arrow_down_probe')
EXERCISE_CHALLENGE_PROBES = points('exercise', 'challenge_probes')
EXERCISE_SWIPE_TO_TOP = (
    *point('exercise', 'swipe_to_top.start'),
    *point('exercise', 'swipe_to_top.end'),
)
EXERCISE_SWIPE_TO_BOTTOM = (
    *point('exercise', 'swipe_to_bottom.start'),
    *point('exercise', 'swipe_to_bottom.end'),
)
EXERCISE_CLICK_RIVAL_INFO = point('exercise', 'click_rival_info')
EXERCISE_CLICK_START_BATTLE = point('exercise', 'click_start_battle')
EXERCISE_SWIPE_DELAY = 0.8


__all__ = [
    'CLICK_CHALLENGE',
    'EXERCISE_ARROW_DOWN_PROBE',
    'EXERCISE_ARROW_GRAY',
    'EXERCISE_ARROW_TOLERANCE',
    'EXERCISE_ARROW_UP_PROBE',
    'EXERCISE_CHALLENGE_COLOR',
    'EXERCISE_CHALLENGE_PROBES',
    'EXERCISE_CHALLENGE_TOLERANCE',
    'EXERCISE_CLICK_RIVAL_INFO',
    'EXERCISE_CLICK_START_BATTLE',
    'EXERCISE_SWIPE_DELAY',
    'EXERCISE_SWIPE_TO_BOTTOM',
    'EXERCISE_SWIPE_TO_TOP',
    'RIVAL_POSITIONS',
]
