"""Compatibility alias for the infra ship-list helpers."""

import sys
from importlib import import_module


sys.modules[__name__] = import_module('autowsgr.infra.ui.ship_list')
