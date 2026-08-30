"""UI calibration accessors backed by read-only data files.

Submodules stay lazy so reading one coordinate does not initialize OCR, color
conversion, or template resources that the caller does not need.
"""

from autowsgr.infra.ui.profile.loader import get


__all__ = ['get']
