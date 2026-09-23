"""Navigation facts stored in the dispatch-owned task Context."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HomeCheckObservation:
    """One homepage checker attempt and its overlay handling result."""

    matched: bool
    overlay_handled: bool
    attempt: int

    def __post_init__(self) -> None:
        if isinstance(self.attempt, bool) or not isinstance(self.attempt, int) or self.attempt < 1:
            raise ValueError('attempt must be a positive integer')


__all__ = ['HomeCheckObservation']
