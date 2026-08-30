"""Compatibility exports for :mod:`autowsgr.business.combat.fleet`."""

import sys

from autowsgr.business.combat import fleet as _module


sys.modules[__name__] = _module
