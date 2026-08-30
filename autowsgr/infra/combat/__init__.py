"""Compatibility exports for :mod:`autowsgr.application.combat`."""

from autowsgr.application.combat import *  # noqa: F403
from autowsgr.application.combat import __all__ as _application_all
from autowsgr.business.combat import *  # noqa: F403
from autowsgr.business.combat import __all__ as _business_all
from autowsgr.business.combat.fleet import (
    ALLOWED_SHIP_TYPE_CODES,
    FleetPreset,
    FleetSelectionSource,
    FleetSlotRule,
    ResolvedFleetSelection,
    ShipSelector,
    exact_fleet_rules,
    fleet_slot_from_api,
    resolve_fleet_selection,
)


__all__ = [
    *_application_all,
    *_business_all,
    'ALLOWED_SHIP_TYPE_CODES',
    'FleetPreset',
    'FleetSelectionSource',
    'FleetSlotRule',
    'ResolvedFleetSelection',
    'ShipSelector',
    'exact_fleet_rules',
    'fleet_slot_from_api',
    'resolve_fleet_selection',
]
