"""Compatibility alias for :mod:`autowsgr.application.ui.pages.build_page`."""

import sys

from autowsgr.application.ui.pages import build_page as _module


sys.modules[__name__] = _module
