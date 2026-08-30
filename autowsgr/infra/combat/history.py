"""Compatibility alias for :mod:`autowsgr.application.combat.history`."""

import sys

from autowsgr.application.combat import history as _module


sys.modules[__name__] = _module
