"""Compatibility package alias for :mod:`autowsgr.application.ui.pages`."""

import sys

from autowsgr.application.ui import pages as _pages


sys.modules[__name__] = _pages
