"""Compatibility alias for :mod:`autowsgr.application.combat.recognition`."""

import sys

from autowsgr.application.combat import recognition as _module


sys.modules[__name__] = _module
