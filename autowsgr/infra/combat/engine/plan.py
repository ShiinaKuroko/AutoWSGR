"""Compatibility alias for :mod:`autowsgr.application.combat.engine.plan`."""

import sys

from autowsgr.application.combat.engine import plan as _module


sys.modules[__name__] = _module
