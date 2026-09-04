"""兼容 shim — 实现已迁移至 :mod:`autowsgr.application.ui.pages.main_page.overlays`。"""

from autowsgr.application.ui.pages.main_page.constants import (
    DismissCoord,
    OverlayKind,
    Sig,
)
from autowsgr.application.ui.pages.main_page.overlays import (
    detect_overlay,
    dismiss_booking,
    dismiss_news,
    dismiss_overlay,
    dismiss_sign,
    dismiss_user_info,
)


__all__ = [
    'DismissCoord',
    'OverlayKind',
    'Sig',
    'detect_overlay',
    'dismiss_booking',
    'dismiss_news',
    'dismiss_overlay',
    'dismiss_sign',
    'dismiss_user_info',
]
