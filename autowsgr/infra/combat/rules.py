"""Compatibility alias for :mod:`autowsgr.application.combat.rules`."""

import sys

from autowsgr.application.combat import rules as _module


sys.modules[__name__] = _module
