"""Initialization templates for dispatch task contexts."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ContextFieldError


@dataclass(frozen=True, slots=True)
class ContextTemplate:
    """Immutable seed describing the current task context."""

    task_type: str

    def __post_init__(self) -> None:
        if not isinstance(self.task_type, str) or not self.task_type.strip():
            raise ContextFieldError('task_type 必须是非空字符串')
        object.__setattr__(self, 'task_type', self.task_type.strip())

    @classmethod
    def for_task(cls, task_type: str) -> ContextTemplate:
        """Create the default context template for a task type."""
        return cls(task_type=task_type)


__all__ = ['ContextTemplate']
