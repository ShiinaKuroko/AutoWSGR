"""编队基建公开入口。"""

from autowsgr.infra.fleet.model import (
    ALLOWED_SHIP_TYPE_CODES,
    NATIVE_VESSEL_TYPE_BY_CODE,
    FleetPreset,
    FleetSelectionSource,
    FleetSlotRule,
    ResolvedFleetSelection,
    ShipSelector,
    exact_fleet_rules,
    fleet_presets_from_yaml,
    fleet_slot_from_api,
    fleet_slot_from_yaml,
    resolve_fleet_selection,
    ship_type_from_native,
    validate_fleet_selection_arguments,
)
from autowsgr.infra.fleet.policy import FLEET_POLICIES, FleetPolicy


__all__ = [
    'ALLOWED_SHIP_TYPE_CODES',
    'FLEET_POLICIES',
    'NATIVE_VESSEL_TYPE_BY_CODE',
    'FleetPolicy',
    'FleetPreset',
    'FleetSelectionSource',
    'FleetSlotRule',
    'ResolvedFleetSelection',
    'ShipSelector',
    'exact_fleet_rules',
    'fleet_presets_from_yaml',
    'fleet_slot_from_api',
    'fleet_slot_from_yaml',
    'resolve_fleet_selection',
    'ship_type_from_native',
    'validate_fleet_selection_arguments',
]
