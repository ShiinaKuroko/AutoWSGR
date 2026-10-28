"""模块功能：定义执行器与调度器之间的任务控制信号。

上层调用：
- dispatch.executor：在安全断点抛出暂停或停止信号，交回执行权。
- dispatch.processor：捕获信号并转换任务状态。

下层依赖：
- Python 内置异常。

本模块只定义任务控制流的信号类型，不承载错误文本、恢复策略或任务状态；这些信号
不属于 common.system 的错误树。
"""

from __future__ import annotations


class TaskPaused(Exception):  # noqa: N818 - public task protocol name
    """执行器在安全断点暂停，交回调度器处理。"""


class TaskStopped(Exception):  # noqa: N818 - public task protocol name
    """执行器收到停止请求，结束当前任务。"""


__all__ = ['TaskPaused', 'TaskStopped']
