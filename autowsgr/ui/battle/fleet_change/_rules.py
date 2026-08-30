"""Compatibility alias for migrated fleet rules."""

import sys
from importlib import import_module


sys.modules[__name__] = import_module(
    'autowsgr.application.ui.pages.battle_preparation.fleet_change._rules',
)
