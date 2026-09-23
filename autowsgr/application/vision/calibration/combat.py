"""战斗页面状态识别的像素校准值。"""

from __future__ import annotations

from autowsgr.common.vision.pixel import MatchStrategy, PixelRule, PixelSignature
from autowsgr.common.vision.roi import ROI


CHOOSE_FORMATION_SIGNATURE = PixelSignature(
    name='choose_formation',
    strategy=MatchStrategy.ALL,
    rules=[
        PixelRule.of(0.9413, 0.2011, (227, 227, 227), tolerance=30.0),
        PixelRule.of(0.9375, 0.3644, (227, 227, 227), tolerance=30.0),
        PixelRule.of(0.9569, 0.5278, (227, 227, 227), tolerance=30.0),
        PixelRule.of(0.5050, 0.5678, (24, 101, 181), tolerance=30.0),
        PixelRule.of(0.5019, 0.9478, (26, 103, 183), tolerance=30.0),
        PixelRule.of(0.8531, 0.9367, (32, 134, 219), tolerance=30.0),
    ],
)

ENEMY_SCAN_AREAS = {
    'exercise': [
        (277, 312, 309, 328),
        (380, 312, 412, 328),
        (483, 312, 515, 328),
        (587, 312, 619, 328),
        (690, 312, 722, 328),
        (793, 312, 825, 328),
    ],
    'fight': [
        (39, 156, 71, 172),
        (322, 156, 354, 172),
        (39, 245, 71, 261),
        (322, 245, 354, 261),
        (39, 334, 71, 350),
        (322, 334, 354, 350),
    ],
}
FORMATION_ROI = ROI(0.11, 0.05, 0.20, 0.15)
FORMATION_ALLOWLIST = '单纵复轮型梯形横阵'
FORMATION_NAMES = {
    '单纵': '单纵阵',
    '复纵': '复纵阵',
    '轮型': '轮型阵',
    '梯形': '梯形阵',
    '单横': '单横阵',
}
RESULT_BLOOD_BAR_PROBE = {
    0: (60 / 960, 142 / 540),
    1: (60 / 960, 217 / 540),
    2: (60 / 960, 292 / 540),
    3: (60 / 960, 367 / 540),
    4: (60 / 960, 442 / 540),
    5: (60 / 960, 517 / 540),
}
SHIP_DROP_PAGE_SIGNATURE = PixelSignature(
    name='ship_drop_page',
    strategy=MatchStrategy.ALL,
    rules=[
        PixelRule.of(0.0500, 0.9500, (20, 40, 68), tolerance=15.0),
        PixelRule.of(0.9500, 0.9500, (12, 35, 60), tolerance=15.0),
        PixelRule.of(0.9070, 0.1569, (16, 26, 46), tolerance=15.0),
        PixelRule.of(0.8906, 0.0972, (20, 26, 45), tolerance=15.0),
        PixelRule.of(0.8016, 0.2361, (33, 82, 125), tolerance=30.0),
        PixelRule.of(0.8016, 0.2361, (33, 82, 125), tolerance=30.0),
        PixelRule.of(0.8300, 0.3000, (253, 236, 166), tolerance=15.0),
        PixelRule.of(0.8719, 0.2333, (23, 41, 67), tolerance=15.0),
        PixelRule.of(0.8109, 0.2681, (36, 58, 72), tolerance=30.0),
    ],
)
SHIP_NAME_CROP = (0.754, 0.268, 0.983, 0.009, 25)
SHIP_TYPE_CROP = (0.79, 0.29, 0.95, 0.1, 25)
SHIP_SLOT_Y = [142 / 540, 217 / 540, 292 / 540, 367 / 540, 442 / 540, 517 / 540]


__all__ = [
    'CHOOSE_FORMATION_SIGNATURE',
    'ENEMY_SCAN_AREAS',
    'FORMATION_ALLOWLIST',
    'FORMATION_NAMES',
    'FORMATION_ROI',
    'RESULT_BLOOD_BAR_PROBE',
    'SHIP_DROP_PAGE_SIGNATURE',
    'SHIP_NAME_CROP',
    'SHIP_SLOT_Y',
    'SHIP_TYPE_CROP',
]
