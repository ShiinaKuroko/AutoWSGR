"""Canteen page calibration used by the canteen Controller.

Coordinates come from ``common/data/calibration/coordinates/canteen.yaml``.
"""

from autowsgr.common.calibration.coordinates import point


CLICK_BACK = point('canteen', 'back')
RECIPE_POSITIONS = {index: point('canteen', f'recipes.{index}') for index in (1, 2, 3)}
CLICK_FORCE_COOK = point('canteen', 'force_cook')
CLICK_CANCEL_COOK = point('canteen', 'cancel_cook')
CLICK_DISMISS_POPUP = point('canteen', 'dismiss_popup')
CLICK_SKIP_ANIMATION = point('canteen', 'skip_animation')


__all__ = [
    'CLICK_BACK',
    'CLICK_CANCEL_COOK',
    'CLICK_DISMISS_POPUP',
    'CLICK_FORCE_COOK',
    'CLICK_SKIP_ANIMATION',
    'RECIPE_POSITIONS',
]
