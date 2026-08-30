"""Compatibility alias for migrated battle-preparation constants."""

import sys
from importlib import import_module


sys.modules[__name__] = import_module(
    'autowsgr.infra.base.combat.battle_preparation.constants',
)
