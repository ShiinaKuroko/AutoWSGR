"""Compatibility package alias for :mod:`autowsgr.application.ui.navigation`."""

import sys

from autowsgr.application.ui import navigation as _navigation


sys.modules[__name__] = _navigation
