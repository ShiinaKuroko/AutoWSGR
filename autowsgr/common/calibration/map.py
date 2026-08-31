"""地图页面的物理坐标。"""

from __future__ import annotations

from autowsgr.common.calibration.colors import color, tolerance
from autowsgr.common.calibration.coordinates import point, points
from autowsgr.common.calibration.ocr import param as ocr_param


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


__all__ = [
    'CAMPAIGN_POSITIONS',
    'CAMPAIGN_REMAIN_CROP',
    'CLICK_BACK',
    'CLICK_DIFFICULTY',
    'DIFFICULTY_EASY_COLOR',
    'DIFFICULTY_EASY_TOLERANCE',
    'DIFFICULTY_HARD_COLOR',
    'DIFFICULTY_HARD_TOLERANCE',
    'PANEL_POSITIONS',
]
