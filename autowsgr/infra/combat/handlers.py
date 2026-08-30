"""Compatibility alias for :mod:`autowsgr.application.combat.handlers`."""

import sys

from autowsgr.application.combat import handlers as _module


sys.modules[__name__] = _module
