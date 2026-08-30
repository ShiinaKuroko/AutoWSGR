"""Compatibility aliases for :mod:`autowsgr.application.combat.engine`."""

import importlib
import sys

from autowsgr.application.combat import engine as _engine


sys.modules[__name__] = _engine
for _name in ('engine', 'plan', 'state'):
    sys.modules[f'{__name__}.{_name}'] = importlib.import_module(
        f'autowsgr.application.combat.engine.{_name}'
    )
