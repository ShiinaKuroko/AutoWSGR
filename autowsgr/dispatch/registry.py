"""执行器注册表 — task_type → 执行器类。"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import threading
    from collections.abc import Callable

    from autowsgr.application.runtime import RuntimeContext as GameContext
    from autowsgr.application.runtime.executor import BaseExecutor


# task_type → (业务执行器模块, 类名)。只在真正执行时加载业务包。
_TASK_MODULES: dict[str, tuple[str, str]] = {
    'campaign': ('autowsgr.business.combat.campaign.executor', 'CampaignExecutor'),
    'decisive': ('autowsgr.business.combat.decisive.executor', 'DecisiveExecutor'),
    'exercise': ('autowsgr.business.combat.exercise.executor', 'ExerciseExecutor'),
    'expedition_check': (
        'autowsgr.business.logistics.expedition',
        'ExpeditionCheckExecutor',
    ),
    'reward_check': ('autowsgr.business.logistics.reward', 'RewardCheckExecutor'),
}

# 已加载的执行器类。
_EXECUTORS: dict[str, type[BaseExecutor]] = {}


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
    """按 task_type 构造执行器，业务模块按需延迟加载。"""
    if task_type not in _EXECUTORS:
        target = _TASK_MODULES.get(task_type)
        if target is None:
            available = ', '.join(sorted({*_EXECUTORS, *_TASK_MODULES})) or '(空)'
            msg = f'未注册的链路: {task_type} (可用: {available})'
            raise KeyError(msg)
        module_name, class_name = target
        module = importlib.import_module(module_name)
        try:
            executor_cls = getattr(module, class_name)
        except AttributeError as exc:
            raise TypeError(f'执行器模块缺少 {class_name}: {module_name}') from exc
        if not isinstance(executor_cls, type):
            raise TypeError(f'执行器不是类: {module_name}.{class_name}')
        _EXECUTORS[task_type] = executor_cls
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
