"""Dispatch-owned task context public entry."""

from __future__ import annotations

from .contracts.navigation import HomeCheckObservation
from .errors import ContextClosedError, ContextError, ContextFieldError, ContextNotBoundError
from .manager import ContextHandle, ContextManager
from .template import ContextTemplate


context = ContextManager()


__all__ = [
    'ContextClosedError',
    'ContextError',
    'ContextFieldError',
    'ContextHandle',
    'ContextManager',
    'ContextNotBoundError',
    'ContextTemplate',
    'HomeCheckObservation',
    'context',
]
