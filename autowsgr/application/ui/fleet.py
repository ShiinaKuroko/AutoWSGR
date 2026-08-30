"""Application input shapes for page-level fleet actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ShipSelector:
    """Fields consumed by the choose-ship page."""

    name: str
    search_name: str | None = None
    ship_types: tuple[Any, ...] = ()
    min_level: int | None = None
    max_level: int | None = None
    relaxed_constraints: bool = False


@dataclass(frozen=True, slots=True)
class FleetSlotRule:
    """Primary and fallback selectors consumed by fleet actions."""

    primary: ShipSelector | None = None
    candidates: tuple[ShipSelector, ...] = ()

    @property
    def options(self) -> tuple[ShipSelector, ...]:
        return (self.primary, *self.candidates) if self.primary is not None else self.candidates


def exact_fleet_rules(names: tuple[str, ...] | list[str]) -> tuple[FleetSlotRule, ...]:
    """Build page input rules for an exact fleet selection."""
    return tuple(FleetSlotRule(primary=ShipSelector(name=name)) for name in names)
