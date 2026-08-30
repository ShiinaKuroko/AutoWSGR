"""Compatibility aliases for :mod:`autowsgr.common.vision`."""

import importlib
import sys

from autowsgr.common import vision as _vision


_SUBMODULES = (
    'api_dll',
    'easyocr_models_checker',
    'easyocr_models_cli',
    'image_matcher',
    'image_template',
    'matcher',
    'ocr',
    'ocr_rules',
    'page_match',
    'pixel',
    'roi',
    'resources',
    'resources._lazy',
    'resources.combat',
    'resources.keys',
    'resources.ops',
    'resources.pages',
    'resources.pages.bath',
    'resources.pages.common',
    'resources.pages.decisive',
    'resources.pages.event',
    'resources.pages.main_page',
)
for _name in _SUBMODULES:
    _module = importlib.import_module(f'autowsgr.common.vision.{_name}')
    sys.modules[f'{__name__}.{_name}'] = _module

globals().update({name: getattr(_vision, name) for name in _vision.__all__})
__all__ = _vision.__all__
