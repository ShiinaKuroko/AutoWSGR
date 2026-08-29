"""Compatibility alias for the migrated battle-preparation blood helpers."""

import sys
from importlib import import_module


sys.modules[__name__] = import_module(
    'autowsgr.infra.base.ui.pages.battle_preparation.blood',
)
