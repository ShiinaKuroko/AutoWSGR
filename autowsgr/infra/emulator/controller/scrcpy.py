"""Compatibility alias for :mod:`autowsgr.common.device.controller.scrcpy`."""

import sys

from autowsgr.common.device.controller import scrcpy as _module


sys.modules[__name__] = _module
