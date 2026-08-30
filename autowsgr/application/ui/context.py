"""Structural context required by application UI capabilities."""

from __future__ import annotations

from typing import Any, Protocol


class UIContext(Protocol):
    """Runtime handles exposed to page actions."""

    ctrl: Any
    config: Any
    ocr: Any
    ship_ocr: Any
    ui_stack: Any
    current_page: Any
