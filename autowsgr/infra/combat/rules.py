"""Compatibility alias for :mod:`autowsgr.business.combat.rules`."""

import sys

from autowsgr.business.combat import rules as _module


sys.modules[__name__] = _module
