"""统一调度模块 — 所有请求的必经大脑。

模块组成:
    processor.py  处理器: 请求模型 + 优先级队列 + 打断决策
    registry.py   执行器注册表: task_type → 执行器类 (业务模块自注册)

配合 business.base.BaseExecutor (执行器基类: _wait 断点 + 暂停协议)。
"""

from autowsgr.dispatch.processor import (
    MAX_PRIORITY,
    TASK_PRIORITIES,
    Processor,
    Request,
    TaskPaused,
    TaskStopped,
    priority_for,
)
from autowsgr.dispatch.registry import build_executor, register, registered_names


__all__ = [
    'MAX_PRIORITY',
    'TASK_PRIORITIES',
    'Processor',
    'Request',
    'TaskPaused',
    'TaskStopped',
    'build_executor',
    'priority_for',
    'register',
    'registered_names',
]
