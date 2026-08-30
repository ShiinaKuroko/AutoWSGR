"""Compatibility alias for :mod:`autowsgr.business.combat.plan`."""

import sys

from autowsgr.business.combat import plan as _module


sys.modules[__name__] = _module
