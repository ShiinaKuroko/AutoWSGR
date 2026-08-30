"""Compatibility alias for :mod:`autowsgr.common.device.os_control.windows`."""

import sys

from autowsgr.common.device.os_control import windows as _module


sys.modules[__name__] = _module
