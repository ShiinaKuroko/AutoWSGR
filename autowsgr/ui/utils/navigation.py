"""Compatibility alias for the infra UI interaction helpers."""

import sys
from importlib import import_module


sys.modules[__name__] = import_module('autowsgr.infra.base.ui.interaction')
