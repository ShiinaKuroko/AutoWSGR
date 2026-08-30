"""Compatibility package aliases for :mod:`autowsgr.application.ui.pages`."""

import importlib
import pkgutil
import sys

from autowsgr.application.ui import pages as _pages


sys.modules[__name__] = _pages

for _info in pkgutil.walk_packages(_pages.__path__, f'{_pages.__name__}.'):
    _module = importlib.import_module(_info.name)
    _alias = _info.name.replace(_pages.__name__, __name__, 1)
    sys.modules[_alias] = _module
