"""Errors raised by the dispatch-owned task context."""

from __future__ import annotations

from autowsgr.common.system.errors import DispatchError


class ContextError(DispatchError):
    """Base error for invalid dispatch Context usage."""


class ContextNotBoundError(ContextError):
    """No task scope is bound to the current execution flow."""


class ContextClosedError(ContextError):
    """The requested task context has already been closed."""


class ContextFieldError(ContextError):
    """A context fact is missing or has an invalid value."""


class ContextScopeError(ContextError):
    """The requested context scope is invalid or conflicts with an active scope."""


__all__ = [
    'ContextClosedError',
    'ContextError',
    'ContextFieldError',
    'ContextNotBoundError',
    'ContextScopeError',
]
