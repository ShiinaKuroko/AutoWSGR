"""Compatibility alias for :mod:`autowsgr.application.ui.ship_list`."""

import sys

from autowsgr.application.ui import ship_list as _module


sys.modules[__name__] = _module
