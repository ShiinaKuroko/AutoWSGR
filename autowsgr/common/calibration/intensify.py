"""Intensify page calibration used by the intensify Controller."""

from autowsgr.common.calibration.coordinates import point


CLICK_BACK = point('intensify', 'back')
TAB_POSITIONS = {
    name: point('intensify', f'tabs.{name}') for name in ('intensify', 'remake', 'skill')
}


__all__ = ['CLICK_BACK', 'TAB_POSITIONS']
