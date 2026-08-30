"""Compatibility alias for :mod:`autowsgr.application.combat.node_tracker`."""

import sys

from autowsgr.application.combat import node_tracker as _module


sys.modules[__name__] = _module
