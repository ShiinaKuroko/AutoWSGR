"""Backyard page calibration used by the backyard Controller.

Coordinates come from ``common/data/calibration/coordinates/backyard.yaml``.
The Controller owns backyard targets and page transitions; this module only
turns calibrated points into values accepted by the device controller.
"""

from autowsgr.common.calibration.coordinates import point


CLICK_BACK = point('backyard', 'back')
NAV_POSITIONS = {
    name: point('backyard', f'nav.{name}') for name in ('bath', 'canteen')
}


__all__ = ['CLICK_BACK', 'NAV_POSITIONS']
