"""Compatibility alias for :mod:`autowsgr.common.calibration.ocr`."""

import sys

from autowsgr.common.calibration import ocr as _module


sys.modules[__name__] = _module
