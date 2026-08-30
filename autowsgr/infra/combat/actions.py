"""Compatibility alias for :mod:`autowsgr.application.combat.actions`."""

import sys

from autowsgr.application.combat import actions as _module


sys.modules[__name__] = _module
