"""Compatibility alias for :mod:`autowsgr.application.combat.recognizer`."""

import sys

from autowsgr.application.combat import recognizer as _module


sys.modules[__name__] = _module
