"""Compatibility package aliases for :mod:`autowsgr.application.ui.navigation`."""

import importlib
import pkgutil
import sys

from autowsgr.application.ui import navigation as _navigation


sys.modules[__name__] = _navigation

for _info in pkgutil.walk_packages(_navigation.__path__, f'{_navigation.__name__}.'):
    _module = importlib.import_module(_info.name)
    _alias = _info.name.replace(_navigation.__name__, __name__, 1)
    sys.modules[_alias] = _module
