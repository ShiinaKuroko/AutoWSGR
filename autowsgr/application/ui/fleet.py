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

    def __eq__(self, other: object) -> bool:
        """Compare with the business rule DTO without importing it."""
        return (
            other.__class__.__name__ == 'ShipSelector'
            and self.name == getattr(other, 'name', None)
            and self.search_name == getattr(other, 'search_name', None)
            and self.ship_types == getattr(other, 'ship_types', None)
            and self.min_level == getattr(other, 'min_level', None)
            and self.max_level == getattr(other, 'max_level', None)
            and self.relaxed_constraints == getattr(other, 'relaxed_constraints', None)
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.name,
                self.search_name,
                self.ship_types,
                self.min_level,
                self.max_level,
                self.relaxed_constraints,
            )
        )


@dataclass(frozen=True, slots=True)
class FleetSlotRule:
    """Primary and fallback selectors consumed by fleet actions."""

    primary: ShipSelector | None = None
    candidates: tuple[ShipSelector, ...] = ()

    def __eq__(self, other: object) -> bool:
        """Compare structurally with the business fleet rule DTO."""
        return (
            other.__class__.__name__ == 'FleetSlotRule'
            and self.primary == getattr(other, 'primary', None)
            and self.candidates == getattr(other, 'candidates', None)
        )

    def __hash__(self) -> int:
        return hash((self.primary, self.candidates))

    @property
    def options(self) -> tuple[ShipSelector, ...]:
        return (self.primary, *self.candidates) if self.primary is not None else self.candidates


def exact_fleet_rules(names: tuple[str, ...] | list[str]) -> tuple[FleetSlotRule, ...]:
    """Build page input rules for an exact fleet selection."""
    return tuple(FleetSlotRule(primary=ShipSelector(name=name)) for name in names)
