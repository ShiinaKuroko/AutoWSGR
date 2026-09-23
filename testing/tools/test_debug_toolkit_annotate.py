"""Tests for the quick ROI and pixel annotation command."""

from __future__ import annotations

import argparse

import numpy as np
import pytest

from tools.debug_toolkit.function.annotate import (
    POINT_COLORS,
    _parse_labeled_point,
    _parse_labeled_roi,
    _parse_point_size,
    annotate_image,
)


def test_parse_labeled_marks() -> None:
    assert _parse_labeled_roi('main:0.1,0.2,0.3,0.4') == ('main', (0.1, 0.2, 0.3, 0.4))
    assert _parse_labeled_point('P1:0.25,0.75') == ('P1', (0.25, 0.75))


@pytest.mark.parametrize('value', ['0', '4', 'two'])
def test_point_size_is_limited_to_three_pixels(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_point_size(value)


def test_annotation_marks_a_single_pixel_without_mutating_source() -> None:
    image = np.zeros((10, 10, 3), dtype=np.uint8)

    marked = annotate_image(image, (), (('', (0.5, 0.5)),), point_size=1)

    assert tuple(marked[5, 5]) == POINT_COLORS[0]
    assert np.count_nonzero(image) == 0
