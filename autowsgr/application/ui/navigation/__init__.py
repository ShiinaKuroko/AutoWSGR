"""Stable package facade for the temporary navigator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.types import NavigationResult, PageMatch, PageName


if TYPE_CHECKING:
    from autowsgr.application.ui.controller.context import UIContext


def goto_page(
    ctx: UIContext,
    target: PageName,
    *,
    attempts: int = 3,
    interval_seconds: float = 0.5,
) -> NavigationResult:
    """Delegate to the navigator with injected recognition parameters."""
    from autowsgr.application.ui.navigation.service import goto_page as _goto_page

    return _goto_page(
        ctx,
        target,
        attempts=attempts,
        interval_seconds=interval_seconds,
    )


__all__ = ['NavigationResult', 'PageMatch', 'PageName', 'goto_page']
