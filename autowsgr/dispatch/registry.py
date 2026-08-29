"""执行器注册表 — task_type → 执行器类。

业务模块 import 时调用 :func:`register` 自注册; 处理器按 task_type 构造执行器。
``_TASK_MODULES`` 声明 task_type → 业务模块路径, 首次使用时延迟 import
(避免 dispatch ↔ business 的循环依赖, 也让进程只加载用到的业务)。
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import threading
    from collections.abc import Callable

    from autowsgr.business.base import BaseExecutor
    from autowsgr.context import GameContext


# task_type → 执行器所在的业务模块 (首次使用时延迟 import 并自注册)
_TASK_MODULES: dict[str, str] = {
    'exercise': 'autowsgr.business.combat.exercise',
    'expedition_check': 'autowsgr.business.logistics.expedition',
    'reward_check': 'autowsgr.business.logistics.reward',
}

# 已加载的执行器类 (业务模块 import 时通过 register() 填充)
_EXECUTORS: dict[str, type[BaseExecutor]] = {}


def register(task_type: str, executor_cls: type[BaseExecutor]) -> None:
    """注册执行器类 (业务模块 import 时调用)。"""
    if task_type in _EXECUTORS:
        msg = f'执行器已注册: {task_type}'
        raise ValueError(msg)
    _EXECUTORS[task_type] = executor_cls


def build_executor(
    task_type: str,
    ctx: GameContext,
    params: dict | None = None,
    *,
    pause: threading.Event | None = None,
    stop: threading.Event | None = None,
    progress: dict | None = None,
    on_event: Callable[..., None] | None = None,
) -> BaseExecutor:
    """按 task_type 构造执行器 (未加载的业务模块在此延迟 import)。"""
    if task_type not in _EXECUTORS:
        module = _TASK_MODULES.get(task_type)
        if module is None:
            available = ', '.join(sorted({*_EXECUTORS, *_TASK_MODULES})) or '(空)'
            msg = f'未注册的链路: {task_type} (可用: {available})'
            raise KeyError(msg)
        importlib.import_module(module)  # 触发该模块的 register()
    return _EXECUTORS[task_type](
        ctx,
        params,
        pause=pause,
        stop=stop,
        progress=progress,
        on_event=on_event,
    )


def registered_names() -> tuple[str, ...]:
    """当前可用的全部链路名。"""
    return tuple(sorted({*_EXECUTORS, *_TASK_MODULES}))
