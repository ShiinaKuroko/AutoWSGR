"""Internal state model for a dispatch task context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import threading

    import numpy as np

    from .template import ContextTemplate


@dataclass(frozen=True, slots=True)
class InterruptSignals:
    """dispatch 持有的让路开关，供 ContextHandle.check_interrupt 读取。

    两个字段都是同一个 threading.Event 的引用而不是快照：处理器一置位，
    导航器在下一个断点就能看到，不存在读写窗口。终止时处理器会同时置位两个开关。
    """

    pause: threading.Event
    """暂停或高优先级任务插队时置位。"""

    stop: threading.Event
    """终止时置位。"""


@dataclass(slots=True)
class TaskContextState:
    """Mutable state owned exclusively by ContextManager."""

    task_id: str
    template: ContextTemplate
    interrupt: InterruptSignals | None = None
    latest_screenshot: np.ndarray | None = None
    current_page: str | None = None
    target_page: str | None = None
    route_step: int | None = None
    last_result: Any = None
    last_error: str | None = None
    closed: bool = False


__all__ = ['InterruptSignals', 'TaskContextState']
