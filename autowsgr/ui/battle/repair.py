"""Compatibility alias for migrated battle-preparation repair."""

import sys
from importlib import import_module


sys.modules[__name__] = import_module(
    'autowsgr.application.ui.pages.battle_preparation.repair',
)
