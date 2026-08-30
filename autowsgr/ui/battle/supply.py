"""Compatibility alias for migrated battle-preparation supply."""

import sys
from importlib import import_module


sys.modules[__name__] = import_module(
    'autowsgr.infra.ui.pages.battle_preparation.supply',
)
