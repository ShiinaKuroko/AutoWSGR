"""Calibration shared by tabbed UI Controllers.

The tab probe points, color threshold, crop, and binarization parameters are
loaded from the common tabbed calibration resources. Tab enums stay in the
Controller modules.
"""

from pathlib import Path

from autowsgr.common.calibration.colors import color, tolerance
from autowsgr.common.calibration.ocr import param


TAB_PROBES = [tuple(float(value) for value in pair) for pair in param('tabbed', 'tab_probes')]
TAB_BLUE = color('tabbed', 'tab_blue')
TAB_BLUE_TOLERANCE = tolerance('tabbed', 'tab_blue')
TAB_DARK_MAX = int(param('tabbed', 'tab_dark_max'))
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / 'data' / 'images' / 'ui'
CROP_Y = float(param('tabbed', 'crop_y'))
CROP_X = float(param('tabbed', 'crop_x'))
REFERENCE_WIDTH = int(param('tabbed', 'reference_width'))
REFERENCE_HEIGHT = int(param('tabbed', 'reference_height'))
ADAPTIVE_BLOCK = int(param('tabbed', 'adaptive_block'))
ADAPTIVE_C = int(param('tabbed', 'adaptive_c'))


__all__ = [
    'ADAPTIVE_BLOCK',
    'ADAPTIVE_C',
    'CROP_X',
    'CROP_Y',
    'REFERENCE_HEIGHT',
    'REFERENCE_WIDTH',
    'TAB_BLUE',
    'TAB_BLUE_TOLERANCE',
    'TAB_DARK_MAX',
    'TAB_PROBES',
    'TEMPLATE_DIR',
]
