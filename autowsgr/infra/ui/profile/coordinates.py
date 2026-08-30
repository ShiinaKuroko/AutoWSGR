"""Compatibility alias for :mod:`autowsgr.common.calibration.coordinates`."""

import sys

from autowsgr.common.calibration import coordinates as _module


sys.modules[__name__] = _module
