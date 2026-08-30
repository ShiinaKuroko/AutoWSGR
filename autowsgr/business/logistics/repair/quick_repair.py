"""Compatibility alias for application repair actions."""

import sys

from autowsgr.application.ui.pages.battle_preparation import repair_action as _module

sys.modules[__name__] = _module
