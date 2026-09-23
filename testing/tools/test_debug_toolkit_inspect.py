"""Tests for the unified screenshot inspection command."""

from __future__ import annotations

import argparse

import pytest

from tools.debug_toolkit.function.inspect import _parse_pixel


def test_parse_pixel_accepts_normalized_coordinates() -> None:
    assert _parse_pixel('0.25,0.75') == (0.25, 0.75)


@pytest.mark.parametrize('value', ['0.25', '1.1,0.5', 'bad,0.5'])
def test_parse_pixel_rejects_invalid_coordinates(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_pixel(value)
