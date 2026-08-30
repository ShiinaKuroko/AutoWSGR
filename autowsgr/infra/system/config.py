"""Compatibility module alias for :mod:`autowsgr.common.system.config`."""

import sys

from autowsgr.common.system import config as _module


sys.modules[__name__] = _module
