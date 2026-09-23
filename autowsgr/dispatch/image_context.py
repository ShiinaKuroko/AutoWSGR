"""Temporary runtime context for application image templates."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING

from autowsgr.common.vision.template import load_template as _load_template


if TYPE_CHECKING:
    from collections.abc import Iterator

    from autowsgr.common.vision.template import Template


_TemplateKey = tuple[str, str | None, tuple[int, int]]
_TemplateState = dict[_TemplateKey, 'Template']
_CURRENT_TEMPLATES: ContextVar[_TemplateState | None] = ContextVar(
    '_CURRENT_TEMPLATES',
    default=None,
)


@contextmanager
def image_context() -> Iterator[None]:
    """Open an image-template context with an isolated cache."""
    token = _CURRENT_TEMPLATES.set({})
    try:
        yield
    finally:
        _CURRENT_TEMPLATES.reset(token)


def load_cached_template(
    relative_path: str | Path,
    *,
    name: str | None = None,
    source_resolution: tuple[int, int] = (1280, 720),
) -> Template:
    """Return a cached template or load it through the vision processor."""
    state = _CURRENT_TEMPLATES.get()
    if state is None:
        raise RuntimeError('图片模板必须在 dispatch.image_context 中加载')

    cache = state
    key = (str(relative_path), name, source_resolution)
    template = cache.get(key)
    if template is None:
        template = _load_template(
            relative_path,
            name=name,
            source_resolution=source_resolution,
        )
        cache[key] = template
    return template


class LazyTemplate:
    """Resolve a template through the current dispatch image context."""

    def __init__(
        self,
        relative_path: str | Path,
        name: str | None = None,
        *,
        source_resolution: tuple[int, int] = (1280, 720),
    ) -> None:
        self._path = relative_path
        self._name = name or Path(relative_path).stem
        self._source_resolution = source_resolution

    def __get__(self, obj: object, objtype: type | None = None) -> Template:
        """Resolve the template on first access in the active context."""
        return load_cached_template(
            self._path,
            name=self._name,
            source_resolution=self._source_resolution,
        )


__all__ = ['LazyTemplate', 'image_context', 'load_cached_template']
