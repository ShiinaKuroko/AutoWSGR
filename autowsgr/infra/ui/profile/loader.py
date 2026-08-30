"""Compatibility alias for :mod:`autowsgr.common.calibration.loader`."""

import sys

from autowsgr.common.calibration import loader as _module


sys.modules[__name__] = _module
