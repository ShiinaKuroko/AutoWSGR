"""Compatibility alias for :mod:`autowsgr.common.device.controller.protocol`."""

import sys

from autowsgr.common.device.controller import protocol as _module


sys.modules[__name__] = _module
