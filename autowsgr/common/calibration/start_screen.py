"""Start screen calibration used by the startup Controller."""

from autowsgr.common.calibration.coordinates import point
from autowsgr.common.calibration.signatures import signature


CLICK_ENTER = point('login', 'enter_game')
PAGE_SIGNATURE = signature('start_screen', 'page')


__all__ = ['CLICK_ENTER', 'PAGE_SIGNATURE']
