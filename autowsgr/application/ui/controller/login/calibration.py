"""Start screen calibration used by the startup Controller."""

from autowsgr.application.vision.calibration._loader import point
from autowsgr.application.vision.calibration._loader import signature


CLICK_ENTER = point('login', 'enter_game')
PAGE_SIGNATURE = signature('start_screen', 'page')


__all__ = ['CLICK_ENTER', 'PAGE_SIGNATURE']
