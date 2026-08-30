"""Compatibility alias for :mod:`autowsgr.common.device.os_control.macos`."""

import sys

from autowsgr.common.device.os_control import macos as _module


sys.modules[__name__] = _module
