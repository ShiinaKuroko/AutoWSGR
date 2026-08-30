"""Compatibility alias for migrated fleet detection."""

import sys
from importlib import import_module


sys.modules[__name__] = import_module(
    'autowsgr.infra.base.combat.battle_preparation.fleet_change._detect',
)
