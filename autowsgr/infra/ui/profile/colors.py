"""Compatibility alias for :mod:`autowsgr.common.calibration.colors`."""

import sys

from autowsgr.common.calibration import colors as _module


sys.modules[__name__] = _module
