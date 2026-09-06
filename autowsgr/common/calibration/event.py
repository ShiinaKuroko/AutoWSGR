"""Event map calibration used by the event Controller.

Coordinates and color thresholds come from the event calibration resources.
The Controller still owns event names, difficulty behavior, and node policy.
"""

from autowsgr.common.calibration.colors import color, tolerance
from autowsgr.common.calibration.coordinates import point
from autowsgr.common.calibration.ocr import param as ocr_param
from autowsgr.common.vision.roi import ROI


NODE_POSITIONS = {index: point('event', f'nodes.{index}') for index in range(1, 7)}
NODE_POSITIONS_BY_EVENT = {
    event: {index: point('event', f'nodes_by_event.{event}.{index}') for index in range(1, 7)}
    for event in ('20260730',)
}
CLICK_BACK = point('event', 'back')
CLICK_FIGHT_BUTTON = point('event', 'fight_button')
FIGHT_BUTTON_ROI = ROI.from_tuple(tuple(ocr_param('event', 'fight_button_roi')))
CLICK_CLOSE_NODE_OVERLAY = point('event', 'close_node_overlay')
CLICK_DIFFICULTY = point('event', 'difficulty')
ENTRANCE_ALPHA_PROBE = point('event', 'entrance_alpha')
ENTRANCE_ALPHA_COLOR = color('event', 'entrance_alpha')
ENTRANCE_ALPHA_TOLERANCE = tolerance('event', 'entrance_alpha')
CLICK_ENTRANCE_ALPHA = point('event', 'entrance_alpha')
CLICK_ENTRANCE_BETA = point('event', 'entrance_beta')


__all__ = [
    'CLICK_BACK',
    'CLICK_CLOSE_NODE_OVERLAY',
    'CLICK_DIFFICULTY',
    'CLICK_ENTRANCE_ALPHA',
    'CLICK_ENTRANCE_BETA',
    'CLICK_FIGHT_BUTTON',
    'ENTRANCE_ALPHA_COLOR',
    'ENTRANCE_ALPHA_PROBE',
    'ENTRANCE_ALPHA_TOLERANCE',
    'FIGHT_BUTTON_ROI',
    'NODE_POSITIONS',
    'NODE_POSITIONS_BY_EVENT',
]
