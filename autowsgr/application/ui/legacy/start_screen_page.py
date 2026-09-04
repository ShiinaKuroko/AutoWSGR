"""兼容 shim — 实现已迁移至 :mod:`autowsgr.application.ui.pages.start_screen`。

老代码仍可 ``from autowsgr.application.ui.legacy.start_screen_page import StartScreenPage``，
新代码请直接使用新路径。
"""

from autowsgr.application.ui.pages.start_screen import (
    CLICK_ENTER,
    PAGE_SIGNATURE,
    StartScreenPage,
)


__all__ = [
    'CLICK_ENTER',
    'PAGE_SIGNATURE',
    'StartScreenPage',
]
