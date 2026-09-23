"""Decisive page calibration used by decisive Controllers.

Coordinates, visual thresholds, OCR regions, and pixel signatures are loaded
from the decisive calibration resources. Chapter state and route decisions
remain in the decisive Controller.
"""

import numpy as np

from autowsgr.application.vision.calibration._loader import color, tolerance
from autowsgr.application.vision.calibration._loader import point, points
from autowsgr.application.vision.calibration._loader import param as ocr_param
from autowsgr.application.vision.calibration._loader import signature
from autowsgr.common.vision.operations.template_matching import ROI


CLICK_BACK = point('decisive', 'back')
CLICK_MAP_BACK = point('decisive', 'map_back')
CLICK_CHOOSE_SHIP_BACK = point('decisive', 'choose_ship_back')
CLICK_PREV_CHAPTER = point('decisive', 'prev_chapter')
CLICK_NEXT_CHAPTER = point('decisive', 'next_chapter')
CLICK_ENTER_MAP = point('decisive', 'enter_map')
CLICK_RESET_CHAPTER = point('decisive', 'reset_chapter')
CLICK_BUY_TICKET_OPEN = point('decisive', 'buy_ticket_open')
CLICK_BUY_RESOURCE = {
    name: point('decisive', f'buy_resource.{name}')
    for name in ('oil', 'ammo', 'steel', 'aluminum')
}
CLICK_BUY_CONFIRM = point('decisive', 'buy_confirm')
CLICK_RETREAT_BUTTON = point('decisive', 'retreat_button')
CLICK_SORTIE = point('decisive', 'sortie')
CLICK_FORMATION = point('decisive', 'formation')
CLICK_FLEET_REFRESH = point('decisive', 'fleet_refresh')
CLICK_FLEET_CLOSE = point('decisive', 'fleet_close')
CLICK_LEAVE = point('decisive', 'leave')
CLICK_RETREAT_CONFIRM = point('decisive', 'retreat_confirm')
CLICK_ADVANCE_CONFIRM = point('decisive', 'advance_confirm')
CLICK_USE_LAST_FLEET_CONFIRM = point('decisive', 'use_last_fleet_confirm')
CLICK_REWARD_ACK = point('decisive', 'reward_ack')
CLICK_SKILL = point('decisive', 'skill')
ADVANCE_CARD_POSITIONS = points('decisive', 'advance_cards')

CHAPTER_NUM_AREA = tuple(float(value) for value in ocr_param('decisive', 'chapter_num_area'))
STAGE_CHECK_POINTS = {
    int(stage): [tuple(float(value) for value in pair) for pair in pairs]
    for stage, pairs in ocr_param('decisive', 'stage_check_points').items()
}
STAGE_CHECK_COLOR = color('decisive', 'stage_check')
STAGE_CHECK_TOLERANCE = tolerance('decisive', 'stage_check')
FLEET_CARD_X_POSITIONS = tuple(float(value) for value in ocr_param('decisive', 'fleet_card_x'))
FLEET_CARD_CLICK_Y = float(ocr_param('decisive', 'fleet_card_y'))
SHIP_NAME_X_RANGES = [
    tuple(float(value) for value in pair)
    for pair in ocr_param('decisive', 'ship_name_x_ranges')
]
SHIP_NAME_Y_RANGE = tuple(float(value) for value in ocr_param('decisive', 'ship_name_y_range'))
COST_AREA = tuple(
    tuple(float(value) for value in pair) for pair in ocr_param('decisive', 'cost_area')
)
RESOURCE_AREA = tuple(
    tuple(float(value) for value in pair) for pair in ocr_param('decisive', 'resource_area')
)
SKILL_SHIP_AREA = ROI.from_tuple(tuple(ocr_param('decisive', 'skill_ship_area')))
SHIP_HSV_LO = np.array(ocr_param('decisive', 'ship_hsv_lo'), dtype=np.uint8)
SHIP_HSV_HI = np.array(ocr_param('decisive', 'ship_hsv_hi'), dtype=np.uint8)
SHIP_MIN_AREA = int(ocr_param('decisive', 'ship_min_area'))
NODE_CROP_OFFSET = tuple(float(value) for value in ocr_param('decisive', 'node_crop_offset'))

SIG_FLEET_ACQUISITION = signature('decisive', 'fleet_acquisition')
SIG_CONFIRM_EXIT = signature('decisive', 'confirm_exit')
SIG_ADVANCE_CHOICE = signature('decisive', 'advance_choice')
SIG_MAP_PAGE = signature('decisive', 'map_page')
SKILL_USED = signature('decisive', 'skill_used')


__all__ = [
    'ADVANCE_CARD_POSITIONS',
    'CHAPTER_NUM_AREA',
    'CLICK_ADVANCE_CONFIRM',
    'CLICK_BACK',
    'CLICK_CHOOSE_SHIP_BACK',
    'CLICK_BUY_CONFIRM',
    'CLICK_BUY_RESOURCE',
    'CLICK_BUY_TICKET_OPEN',
    'CLICK_ENTER_MAP',
    'CLICK_FLEET_CLOSE',
    'CLICK_FLEET_REFRESH',
    'CLICK_FORMATION',
    'CLICK_LEAVE',
    'CLICK_MAP_BACK',
    'CLICK_NEXT_CHAPTER',
    'CLICK_PREV_CHAPTER',
    'CLICK_RESET_CHAPTER',
    'CLICK_REWARD_ACK',
    'CLICK_RETREAT_BUTTON',
    'CLICK_RETREAT_CONFIRM',
    'CLICK_SKILL',
    'CLICK_SORTIE',
    'CLICK_USE_LAST_FLEET_CONFIRM',
    'COST_AREA',
    'FLEET_CARD_CLICK_Y',
    'FLEET_CARD_X_POSITIONS',
    'RESOURCE_AREA',
    'SHIP_HSV_HI',
    'SHIP_HSV_LO',
    'SHIP_MIN_AREA',
    'SHIP_NAME_X_RANGES',
    'SHIP_NAME_Y_RANGE',
    'NODE_CROP_OFFSET',
    'SIG_ADVANCE_CHOICE',
    'SIG_CONFIRM_EXIT',
    'SIG_FLEET_ACQUISITION',
    'SIG_MAP_PAGE',
    'SKILL_SHIP_AREA',
    'SKILL_USED',
    'STAGE_CHECK_COLOR',
    'STAGE_CHECK_POINTS',
    'STAGE_CHECK_TOLERANCE',
]
