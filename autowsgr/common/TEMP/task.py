"""任务执行控制契约。"""


class TaskPaused(Exception):  # noqa: N818 - public task protocol name
    """执行器在安全断点暂停，交回调度器处理。"""


class TaskStopped(Exception):  # noqa: N818 - public task protocol name
    """执行器收到停止请求，结束当前任务。"""
