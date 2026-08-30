"""Compatibility alias for :mod:`autowsgr.application.combat.engine.state`."""

import sys

from autowsgr.application.combat.engine import state as _module


sys.modules[__name__] = _module
