"""Compatibility alias for migrated fleet selection."""

import sys
from importlib import import_module


sys.modules[__name__] = import_module(
    'autowsgr.infra.ui.pages.battle_preparation.fleet_change._selection',
)
