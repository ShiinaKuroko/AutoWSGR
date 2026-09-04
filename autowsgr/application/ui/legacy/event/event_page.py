"""Compatibility alias for :mod:`autowsgr.application.ui.pages.event.event_page`."""

import sys

from autowsgr.application.ui.pages.event import event_page as _module


sys.modules[__name__] = _module
