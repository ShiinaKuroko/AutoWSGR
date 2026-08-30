"""Compatibility alias for :mod:`autowsgr.common.device.os_control.base`."""

import sys

from autowsgr.common.device.os_control import base as _module


sys.modules[__name__] = _module
