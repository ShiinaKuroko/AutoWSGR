"""Choose-ship calibration shared by fleet preparation and ship-list OCR.

Coordinates, OCR geometry, and page signatures come from the common
calibration resources. Selection policy stays with the Controller.
"""

from autowsgr.application.vision.calibration._loader import param, point, signature


CLICK_SEARCH_BOX = point('choose_ship', 'search_box')
CLICK_DISMISS_KEYBOARD = point('choose_ship', 'dismiss_keyboard')
CLICK_REMOVE_SHIP = point('choose_ship', 'remove_ship')
SCROLL_FROM_Y = float(param('choose_ship', 'scroll_from_y'))
SCROLL_TO_Y = float(param('choose_ship', 'scroll_to_y'))
SCROLL_X = float(param('choose_ship', 'scroll_x'))
SCROLL_DURATION = float(param('choose_ship', 'scroll_duration'))
CARD_REFERENCE_WIDTH = int(param('choose_ship', 'card_reference_width'))
CARD_REFERENCE_HEIGHT = int(param('choose_ship', 'card_reference_height'))
SHIP_TYPE_CROP_OFFSETS = tuple(param('choose_ship', 'ship_type_crop_offsets'))
SHIP_TYPE_OCR_SCALES = tuple(param('choose_ship', 'ship_type_ocr_scales'))
LEGACY_WIDTH = int(param('choose_ship', 'legacy_width'))
LEGACY_HEIGHT = int(param('choose_ship', 'legacy_height'))
LEGACY_LIST_WIDTH = int(param('choose_ship', 'legacy_list_width'))
SHIP_LEVEL_CROP_OFFSETS = tuple(param('choose_ship', 'ship_level_crop_offsets'))
SHIP_LEVEL_OCR_SCALES = tuple(param('choose_ship', 'ship_level_ocr_scales'))
FLEET_NAME_STRIP_Y = tuple(param('choose_ship', 'fleet_name_strip_y'))
FLEET_SLOT_X_CENTERS = tuple(param('choose_ship', 'fleet_slot_x_centers'))
SHIP_FUZZY_THRESHOLD = int(param('choose_ship', 'ship_fuzzy_threshold'))
PAGE_SIGNATURE = signature('choose_ship', 'page')
INPUT_SIGNATURE = signature('choose_ship', 'input')


__all__ = [
    'CARD_REFERENCE_HEIGHT',
    'CARD_REFERENCE_WIDTH',
    'CLICK_DISMISS_KEYBOARD',
    'CLICK_REMOVE_SHIP',
    'CLICK_SEARCH_BOX',
    'FLEET_NAME_STRIP_Y',
    'FLEET_SLOT_X_CENTERS',
    'INPUT_SIGNATURE',
    'LEGACY_HEIGHT',
    'LEGACY_LIST_WIDTH',
    'LEGACY_WIDTH',
    'PAGE_SIGNATURE',
    'SCROLL_DURATION',
    'SCROLL_FROM_Y',
    'SCROLL_TO_Y',
    'SCROLL_X',
    'SHIP_FUZZY_THRESHOLD',
    'SHIP_LEVEL_CROP_OFFSETS',
    'SHIP_LEVEL_OCR_SCALES',
    'SHIP_TYPE_CROP_OFFSETS',
    'SHIP_TYPE_OCR_SCALES',
]
