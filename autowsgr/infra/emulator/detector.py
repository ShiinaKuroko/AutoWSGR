"""Compatibility alias for :mod:`autowsgr.common.device.detector`."""

import sys

from autowsgr.common.device import detector as _module


sys.modules[__name__] = _module
