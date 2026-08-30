"""UI calibration accessors backed by read-only data files."""

from . import colors, coordinates, ocr, signatures
from .loader import get

__all__ = ['colors', 'coordinates', 'get', 'ocr', 'signatures']
