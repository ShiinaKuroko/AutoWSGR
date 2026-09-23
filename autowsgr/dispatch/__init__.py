"""调度模块及其运行时上下文命名空间。"""

from __future__ import annotations

from importlib import import_module


_EXPORTS = {
    'MAX_PRIORITY': ('autowsgr.dispatch.processor', 'MAX_PRIORITY'),
    'TASK_PRIORITIES': ('autowsgr.dispatch.processor', 'TASK_PRIORITIES'),
    'Processor': ('autowsgr.dispatch.processor', 'Processor'),
    'Request': ('autowsgr.dispatch.processor', 'Request'),
    'TaskPaused': ('autowsgr.dispatch.processor', 'TaskPaused'),
    'TaskStopped': ('autowsgr.dispatch.processor', 'TaskStopped'),
    'priority_for': ('autowsgr.dispatch.processor', 'priority_for'),
    'build_executor': ('autowsgr.dispatch.registry', 'build_executor'),
    'registered_names': ('autowsgr.dispatch.registry', 'registered_names'),
    'LazyTemplate': ('autowsgr.dispatch.image_context', 'LazyTemplate'),
    'image_context': ('autowsgr.dispatch.image_context', 'image_context'),
    'load_cached_template': ('autowsgr.dispatch.image_context', 'load_cached_template'),
}


def __getattr__(name: str) -> object:
    """按需加载调度能力，避免子模块导入触发无关执行器依赖。"""
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    module_name, attribute_name = target
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value


__all__ = list(_EXPORTS)
