"""Compatibility alias for :mod:`autowsgr.common.ui.interaction`."""

import sys

from autowsgr.common.ui import interaction as _module


sys.modules[__name__] = _module
sys.modules[f'{__name__}.navigation'] = _module
