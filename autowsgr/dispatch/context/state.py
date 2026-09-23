"""Internal state model for a dispatch task context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import numpy as np

    from .template import ContextTemplate


@dataclass(slots=True)
class TaskContextState:
    """Mutable state owned exclusively by ContextManager."""

    task_id: str
    template: ContextTemplate
    latest_screenshot: np.ndarray | None = None
    current_page: str | None = None
    target_page: str | None = None
    route_step: int | None = None
    last_result: Any = None
    last_error: str | None = None
    closed: bool = False


__all__ = ['TaskContextState']
