"""Compatibility alias for :mod:`autowsgr.common.calibration.signatures`."""

import sys

from autowsgr.common.calibration import signatures as _module


sys.modules[__name__] = _module
