"""Temporary data helpers awaiting a domain owner."""

from __future__ import annotations


def merge_dicts(base: dict, override: dict) -> dict:
    """Return a recursive merge without mutating either input mapping."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


__all__ = ['merge_dicts']
