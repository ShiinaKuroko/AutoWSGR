"""兼容 shim — 实现已迁移至 :mod:`autowsgr.infra.base.ui.pages.start_screen`。

老代码仍可 ``from autowsgr.ui.start_screen_page import StartScreenPage``，
新代码请直接使用新路径。
"""

from autowsgr.infra.base.ui.pages.start_screen import (
    CLICK_ENTER,
    PAGE_SIGNATURE,
    StartScreenPage,
    _CLICK_SETTLE,
)

__all__ = [
    'CLICK_ENTER',
    'PAGE_SIGNATURE',
    'StartScreenPage',
]
