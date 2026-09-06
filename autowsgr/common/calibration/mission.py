"""Mission page calibration used by mission Controllers and OCR helpers."""

from autowsgr.common.calibration.colors import color, param as color_param, tolerance
from autowsgr.common.calibration.coordinates import point
from autowsgr.common.calibration.ocr import param as ocr_param
from autowsgr.common.vision.roi import ROI


CLICK_BACK = point('mission', 'back')
SCROLL = tuple(float(value) for value in ocr_param('mission', 'scroll'))
SCROLL_DURATION = float(ocr_param('mission', 'scroll_duration'))
SCROLL_DELAY = float(ocr_param('mission', 'scroll_delay'))
GOTO_COLOR = color('mission', 'goto_blue')
GOTO_TOLERANCE = tolerance('mission', 'goto_blue')
CLAIM_R_MIN = color_param('mission', 'claim.r_min')
CLAIM_G_MIN = color_param('mission', 'claim.g_min')
CLAIM_B_MAX = color_param('mission', 'claim.b_max')
BUTTON_SCAN_ROI = ROI.from_tuple(tuple(ocr_param('mission', 'button_scan_roi')))
SCAN_X = float(ocr_param('mission', 'scan_x'))
SCAN_Y_STEP = float(ocr_param('mission', 'scan_y_step'))
CLUSTER_GAP = float(ocr_param('mission', 'cluster_gap'))
MIN_CLUSTER_SIZE = int(ocr_param('mission', 'min_cluster_size'))
WIDE_BTN_CHECK_X = float(ocr_param('mission', 'wide_btn_check_x'))
NAME_CROP_MIN_Y = float(ocr_param('mission', 'name_crop_min_y'))
OCR_CONFIDENCE_MIN = float(ocr_param('mission', 'ocr_confidence_min'))
NAME_ROI_X1 = float(ocr_param('mission', 'name_roi.x1'))
NAME_ROI_X2 = float(ocr_param('mission', 'name_roi.x2'))
NAME_Y_OFFSET = float(ocr_param('mission', 'name_roi.y_offset'))
NAME_ROI_Y_PAD = float(ocr_param('mission', 'name_roi.y_pad'))
PROGRESS_ROI_X1 = float(ocr_param('mission', 'progress_roi.x1'))
PROGRESS_ROI_X2 = float(ocr_param('mission', 'progress_roi.x2'))
PROGRESS_Y_OFFSET = float(ocr_param('mission', 'progress_roi.y_offset'))
PROGRESS_ROI_Y_PAD = float(ocr_param('mission', 'progress_roi.y_pad'))


__all__ = [
    'BUTTON_SCAN_ROI',
    'CLAIM_B_MAX',
    'CLAIM_G_MIN',
    'CLAIM_R_MIN',
    'CLICK_BACK',
    'CLUSTER_GAP',
    'GOTO_COLOR',
    'GOTO_TOLERANCE',
    'MIN_CLUSTER_SIZE',
    'NAME_CROP_MIN_Y',
    'NAME_ROI_X1',
    'NAME_ROI_X2',
    'NAME_ROI_Y_PAD',
    'NAME_Y_OFFSET',
    'OCR_CONFIDENCE_MIN',
    'PROGRESS_ROI_X1',
    'PROGRESS_ROI_X2',
    'PROGRESS_ROI_Y_PAD',
    'PROGRESS_Y_OFFSET',
    'SCAN_X',
    'SCAN_Y_STEP',
    'SCROLL',
    'SCROLL_DELAY',
    'SCROLL_DURATION',
    'WIDE_BTN_CHECK_X',
]
