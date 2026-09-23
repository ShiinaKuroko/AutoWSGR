"""Runtime handles consumed by business use cases.

The concrete session remains owned by the runtime/dispatch layer. This module
only describes the small surface business code needs.
"""

from __future__ import annotations

from typing import Any, Protocol


class RuntimeContext(Protocol):
    """Shared runtime handles and state operations."""

    ctrl: Any
    config: Any
    ocr: Any
    ship_ocr: Any
    ui_stack: Any
    current_page: Any
    daily_overlay_checked: bool
    latest_screenshot: Any

    def record_screenshot(self, screen: Any) -> None:
        """保存识别链路最近一次截图。"""

    def get_ship(self, name: str) -> Any:
        """Return a mutable ship record owned by the runtime session."""

    def update_ship_damage(self, name: str, state: Any) -> None:
        """Update a ship's damage state in the session."""
