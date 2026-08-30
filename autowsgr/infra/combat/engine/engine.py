"""Compatibility alias for :mod:`autowsgr.business.combat.engine`."""

import sys

from autowsgr.business.combat import engine as _module


sys.modules[__name__] = _module
