"""Bath page calibration used by the bath Controller.

Coordinates, colors, and OCR geometry come from the bath calibration YAML
files. Page state and repair workflow policy remain in the Controller.
"""

from autowsgr.common.calibration.colors import color, param as color_param, tolerance
from autowsgr.common.calibration.coordinates import point
from autowsgr.common.calibration.ocr import param as ocr_param


CLICK_BACK = point('bath', 'back')
CLICK_REPAIR_ALL = point('bath', 'repair_all')
CLICK_CHOOSE_REPAIR = point('bath', 'choose_repair')
CLICK_CLOSE_OVERLAY = point('bath', 'close_overlay')
CLICK_FIRST_REPAIR_SHIP = point('bath', 'first_repair_ship')
SWIPE_START = point('bath', 'swipe.start')
SWIPE_END = point('bath', 'swipe.end')
SWIPE_DURATION = float(ocr_param('bath', 'swipe_duration'))
SWIPE_DELAY = float(ocr_param('bath', 'swipe_delay'))

BORDER_THRESHOLD = int(ocr_param('bath', 'border_threshold'))
CARD_MIN_WIDTH = int(ocr_param('bath', 'card_geometry.min_width'))
CARD_MAX_WIDTH = int(ocr_param('bath', 'card_geometry.max_width'))
CARD_MIN_HEIGHT = int(ocr_param('bath', 'card_geometry.min_height'))
CARD_MAX_HEIGHT = int(ocr_param('bath', 'card_geometry.max_height'))
FULL_CARD_WIDTH = int(ocr_param('bath', 'card_geometry.full_width'))
FULL_CARD_WIDTH_RATIO = float(ocr_param('bath', 'card_geometry.full_width_ratio'))
EDGE_MARGIN = int(ocr_param('bath', 'edge_margin'))
NAME_Y_MIN = int(ocr_param('bath', 'name_y_min'))
NAME_Y_MAX = int(ocr_param('bath', 'name_y_max'))
NAME_CONFIDENCE_MIN = float(ocr_param('bath', 'name_confidence_min'))
TIME_CROP_Y = int(ocr_param('bath', 'time_crop_y'))
TIME_SCALE = int(ocr_param('bath', 'time_scale'))

_REPAIR_ALL = color_param('bath', 'repair_all_button')
REPAIR_ALL_BUTTON_COLOR = (tuple(_REPAIR_ALL['rgb']), tolerance('bath', 'repair_all_button'))
_CLOSE_OVERLAY = color_param('bath', 'close_overlay_button')
CLOSE_OVERLAY_BUTTON_COLOR = (
    tuple(_CLOSE_OVERLAY['rgb']),
    tolerance('bath', 'close_overlay_button'),
)


__all__ = [
    'BORDER_THRESHOLD',
    'CARD_MAX_HEIGHT',
    'CARD_MAX_WIDTH',
    'CARD_MIN_HEIGHT',
    'CARD_MIN_WIDTH',
    'CLICK_BACK',
    'CLICK_CHOOSE_REPAIR',
    'CLICK_CLOSE_OVERLAY',
    'CLICK_FIRST_REPAIR_SHIP',
    'CLICK_REPAIR_ALL',
    'CLOSE_OVERLAY_BUTTON_COLOR',
    'EDGE_MARGIN',
    'FULL_CARD_WIDTH',
    'FULL_CARD_WIDTH_RATIO',
    'NAME_CONFIDENCE_MIN',
    'NAME_Y_MAX',
    'NAME_Y_MIN',
    'REPAIR_ALL_BUTTON_COLOR',
    'SWIPE_DELAY',
    'SWIPE_DURATION',
    'SWIPE_END',
    'SWIPE_START',
    'TIME_CROP_Y',
    'TIME_SCALE',
]
