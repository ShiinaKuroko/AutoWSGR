"""Compatibility alias for :mod:`autowsgr.application.combat.engine.engine`."""

import sys

from autowsgr.application.combat.engine import engine as _module


sys.modules[__name__] = _module
