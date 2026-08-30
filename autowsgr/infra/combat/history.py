"""Compatibility alias for :mod:`autowsgr.business.combat.history`."""

import sys

from autowsgr.business.combat import history as _module


sys.modules[__name__] = _module
