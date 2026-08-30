"""Compatibility alias for the infra choose-ship page."""

import sys
from importlib import import_module


sys.modules[__name__] = import_module('autowsgr.infra.base.combat.choose_ship')
