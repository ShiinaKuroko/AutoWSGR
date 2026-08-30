"""Compatibility module alias for :mod:`autowsgr.common.system.file_utils`."""

import sys

from autowsgr.common.system import file_utils as _module


sys.modules[__name__] = _module
