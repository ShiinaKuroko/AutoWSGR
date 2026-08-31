"""选船页面的坐标、像素签名和 OCR 校准值。"""

from __future__ import annotations

from autowsgr.common.vision.pixel import MatchStrategy, PixelRule, PixelSignature


CLICK_SEARCH_BOX = (700 / 960, 30 / 540)
CLICK_DISMISS_KEYBOARD = (500 / 960, 50 / 540)
CLICK_REMOVE_SHIP = (83 / 960, 167 / 540)
SCROLL_FROM_Y = 0.55
SCROLL_TO_Y = 0.30
CARD_REFERENCE_WIDTH = 1280
CARD_REFERENCE_HEIGHT = 720
SHIP_TYPE_CROP_OFFSETS = (-62, -59, -13, -34.5)
SHIP_TYPE_OCR_SCALES = (2, 3, 4)
LEGACY_WIDTH = 1280
LEGACY_HEIGHT = 720
LEGACY_LIST_WIDTH = 1048
SHIP_LEVEL_CROP_OFFSETS = (-62, -38, -2, -20)
SHIP_LEVEL_OCR_SCALES = (2, 3, 4)
FLEET_NAME_STRIP_Y = (435 / 720, 462 / 720)
FLEET_SLOT_X_CENTERS = (0.1146, 0.2292, 0.3438, 0.4583, 0.5729, 0.6875)
SHIP_FUZZY_THRESHOLD = 2

PAGE_SIGNATURE = PixelSignature(
    name='choose_ship_page',
    strategy=MatchStrategy.ALL,
    rules=[
        PixelRule.of(0.8594, 0.1514, (31, 46, 69), tolerance=30.0),
        PixelRule.of(0.8602, 0.3167, (31, 139, 238), tolerance=30.0),
        PixelRule.of(0.8578, 0.5306, (57, 57, 57), tolerance=30.0),
        PixelRule.of(0.8594, 0.6736, (54, 54, 54), tolerance=30.0),
        PixelRule.of(0.8656, 0.8014, (35, 57, 81), tolerance=30.0),
    ],
)

INPUT_SIGNATURE = PixelSignature(
    name='choose_ship_input',
    strategy=MatchStrategy.ALL,
    rules=[
        PixelRule.of(0.3109, 0.9417, (253, 253, 253), tolerance=30.0),
        PixelRule.of(0.4437, 0.9417, (253, 253, 253), tolerance=30.0),
        PixelRule.of(0.5883, 0.9347, (253, 253, 253), tolerance=30.0),
    ],
)


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
    'SCROLL_FROM_Y',
    'SCROLL_TO_Y',
    'SHIP_FUZZY_THRESHOLD',
    'SHIP_LEVEL_CROP_OFFSETS',
    'SHIP_LEVEL_OCR_SCALES',
    'SHIP_TYPE_CROP_OFFSETS',
    'SHIP_TYPE_OCR_SCALES',
]
