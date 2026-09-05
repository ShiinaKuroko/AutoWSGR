"""地图页面的物理坐标。"""

from __future__ import annotations

from autowsgr.common.calibration.colors import color, tolerance
from autowsgr.common.calibration.coordinates import point, points
from autowsgr.common.calibration.ocr import param as ocr_param
from autowsgr.common.vision.pixel import Color


CLICK_BACK = point('map', 'back')
PANEL_POSITIONS = {
    name: point('map', f'panel.{name}')
    for name in ('sortie', 'exercise', 'expedition', 'battle', 'decisive')
}

CAMPAIGN_POSITIONS = dict(enumerate(points('map', 'campaign.positions'), 1))
CLICK_DIFFICULTY = point('map', 'campaign.difficulty')
CAMPAIGN_REMAIN_CROP = tuple(ocr_param('campaign', 'remain_crop'))
DIFFICULTY_EASY_COLOR = color('campaign', 'difficulty_easy')
DIFFICULTY_EASY_TOLERANCE = tolerance('campaign', 'difficulty_easy')
DIFFICULTY_HARD_COLOR = color('campaign', 'difficulty_hard')
DIFFICULTY_HARD_TOLERANCE = tolerance('campaign', 'difficulty_hard')


# -- Map page calibration ----------------------------------------------------

EXPEDITION_NOTIF_COLOR = Color.of(245, 88, 47)
EXPEDITION_TOLERANCE = 40.0
EXPEDITION_READY_COLOR = Color.of(253, 228, 66)
EXPEDITION_IDLE_COLOR = Color.of(38, 147, 250)
EXPEDITION_SLOT_TOLERANCE = 30.0
EXPEDITION_NOTIF_PROBE = (0.4953, 0.0213)
EXPEDITION_SLOT_PROBES = [
    (0.8516, 0.2736),
    (0.8531, 0.4736),
    (0.8539, 0.6667),
    (0.8547, 0.8694),
]
TITLE_CROP_REGION = (0.7, 0.18, 0.9, 0.215)
SIDEBAR_SCAN_X = 0.08
SIDEBAR_SCAN_Y_RANGE = (0.12, 0.88)
SIDEBAR_SCAN_STEP = 0.01
SIDEBAR_BRIGHTNESS_THRESHOLD = 150
CHAPTER_SPACING = 0.12
SIDEBAR_CLICK_X = 0.10
CHAPTER_NAV_DELAY = 0.5
CHAPTER_NAV_MAX_ATTEMPTS = 20
CLICK_MAP_NEXT = (937 / 960, 277 / 540)
CLICK_MAP_PREV = (247 / 960, 277 / 540)
CLICK_ENTER_SORTIE = (0.625, 0.556)
CLICK_ENTER_DECISIVE = (0.12, 0.209)
MAP_NODE_POSITIONS = {
    1: (0.500, 0.200),
    2: (0.500, 0.350),
    3: (0.500, 0.500),
    4: (0.500, 0.650),
    5: (0.500, 0.800),
}
CLICK_EXPEDITION_SKIP = (0.76, 0.5)
LOOT_COUNT_CROP = (0.804, 0.025, 0.863, 0.065)
SHIP_COUNT_CROP = (0.904, 0.025, 0.975, 0.064)


__all__ = [
    'CAMPAIGN_POSITIONS',
    'CAMPAIGN_REMAIN_CROP',
    'CHAPTER_NAV_DELAY',
    'CHAPTER_NAV_MAX_ATTEMPTS',
    'CHAPTER_SPACING',
    'CLICK_BACK',
    'CLICK_DIFFICULTY',
    'CLICK_ENTER_DECISIVE',
    'CLICK_ENTER_SORTIE',
    'CLICK_EXPEDITION_SKIP',
    'CLICK_MAP_NEXT',
    'CLICK_MAP_PREV',
    'DIFFICULTY_EASY_COLOR',
    'DIFFICULTY_EASY_TOLERANCE',
    'DIFFICULTY_HARD_COLOR',
    'DIFFICULTY_HARD_TOLERANCE',
    'EXPEDITION_IDLE_COLOR',
    'EXPEDITION_NOTIF_COLOR',
    'EXPEDITION_NOTIF_PROBE',
    'EXPEDITION_READY_COLOR',
    'EXPEDITION_SLOT_PROBES',
    'EXPEDITION_SLOT_TOLERANCE',
    'EXPEDITION_TOLERANCE',
    'LOOT_COUNT_CROP',
    'MAP_NODE_POSITIONS',
    'PANEL_POSITIONS',
    'SHIP_COUNT_CROP',
    'SIDEBAR_BRIGHTNESS_THRESHOLD',
    'SIDEBAR_CLICK_X',
    'SIDEBAR_SCAN_STEP',
    'SIDEBAR_SCAN_X',
    'SIDEBAR_SCAN_Y_RANGE',
    'TITLE_CROP_REGION',
]
