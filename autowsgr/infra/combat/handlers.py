"""Compatibility alias for :mod:`autowsgr.business.combat.handlers`."""

import sys

from autowsgr.business.combat import handlers as _module


sys.modules[__name__] = _module
