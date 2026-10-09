"""Initialization templates for dispatch task contexts."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ContextFieldError


@dataclass(frozen=True, slots=True)
class ContextTemplate:
    """Immutable seed describing the current task context."""

    task_type: str
    event_type: str | None = None
    event_stage: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, 'task_type', _require_text(self.task_type, 'task_type'))
        object.__setattr__(self, 'event_type', _optional_text(self.event_type, 'event_type'))
        object.__setattr__(self, 'event_stage', _optional_text(self.event_stage, 'event_stage'))

    @classmethod
    def for_task(
        cls,
        task_type: str,
        *,
        event_type: str | None = None,
        event_stage: str | None = None,
    ) -> ContextTemplate:
        """Create the default context template for a task type.

        Args:
            task_type: 任务类型，决定执行器链路。
            event_type: 活动玩法标识；非活动任务留空。
            event_stage: 活动章节标识；非活动任务留空。

        Returns:
            任务上下文的初始化模板。
        """
        return cls(task_type=task_type, event_type=event_type, event_stage=event_stage)


def _require_text(value: object, field_name: str) -> str:
    """校验必填文本字段。"""
    if not isinstance(value, str) or not value.strip():
        raise ContextFieldError(f'{field_name} 必须是非空字符串')
    return value.strip()


def _optional_text(value: object, field_name: str) -> str | None:
    """校验可选文本字段，未提供时返回空值。"""
    if value is None:
        return None
    return _require_text(value, field_name)


__all__ = ['ContextTemplate']
