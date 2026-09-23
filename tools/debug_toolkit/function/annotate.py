"""Quickly mark normalized ROIs and pixel probes on a screenshot."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from autowsgr.common.device import adb

from tools.debug_toolkit.function.collect import (
    CropToolError,
    _read_saved_serial,
    _write_png,
)
from tools.debug_toolkit.function.roi import _parse_roi


if TYPE_CHECKING:
    from collections.abc import Sequence


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = PACKAGE_ROOT / 'result' / 'annotate'

ROI_COLORS = (
    (0, 0, 255),
    (0, 165, 255),
    (0, 200, 0),
    (255, 0, 255),
)
POINT_COLORS = (
    (255, 0, 0),
    (255, 255, 0),
    (0, 255, 255),
)

RoiMark = tuple[str, tuple[float, float, float, float]]
PointMark = tuple[str, tuple[float, float]]


def _split_label(value: str) -> tuple[str, str]:
    label, separator, coordinates = value.partition(':')
    if not separator:
        return '', value
    if not coordinates:
        raise argparse.ArgumentTypeError('label must be followed by coordinates')
    return label.strip(), coordinates


def _parse_labeled_roi(value: str) -> RoiMark:
    label, coordinates = _split_label(value)
    return label, _parse_roi(coordinates)


def _parse_labeled_point(value: str) -> PointMark:
    label, coordinates = _split_label(value)
    try:
        values = tuple(float(item.strip()) for item in coordinates.split(','))
    except ValueError as exc:
        raise argparse.ArgumentTypeError('point must be x,y') from exc
    if len(values) != 2 or not all(0.0 <= item <= 1.0 for item in values):
        raise argparse.ArgumentTypeError('point values must be in [0, 1]')
    return label, (values[0], values[1])


def _parse_point_size(value: str) -> int:
    try:
        size = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('point size must be 1, 2, or 3') from exc
    if size not in {1, 2, 3}:
        raise argparse.ArgumentTypeError('point size must be 1, 2, or 3')
    return size


def _parse_line_width(value: str) -> int:
    try:
        width = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('line width must be a positive integer') from exc
    if width <= 0:
        raise argparse.ArgumentTypeError('line width must be a positive integer')
    return width


def _read_image(path: Path) -> np.ndarray:
    """Read an image without losing Windows paths containing non-ASCII text."""
    try:
        encoded = np.fromfile(str(path), dtype=np.uint8)
    except OSError as exc:
        raise CropToolError(f'cannot read image: {path}') from exc
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise CropToolError(f'cannot decode image: {path}')
    return image


def _load_source(args: argparse.Namespace) -> np.ndarray:
    if args.image is not None:
        return _read_image(args.image)
    adb_path = adb.find_adb(args.adb_path)
    return adb.capture_screen(args.serial or _read_saved_serial(), adb_path)


def _put_label(image: np.ndarray, text: str, x: int, y: int, color: tuple[int, int, int]) -> None:
    if not text:
        return
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, text, (x, y), font, 0.5, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(image, text, (x, y), font, 0.5, color, 1, cv2.LINE_AA)


def _pixel_position(width: int, height: int, x: float, y: float) -> tuple[int, int]:
    return min(width - 1, int(x * width)), min(height - 1, int(y * height))


def _draw_roi(
    image: np.ndarray,
    mark: RoiMark,
    index: int,
    color: tuple[int, int, int],
    line_width: int,
) -> None:
    label, (x1, y1, x2, y2) = mark
    height, width = image.shape[:2]
    left, top = int(x1 * width), int(y1 * height)
    right, bottom = min(width - 1, int(x2 * width)), min(height - 1, int(y2 * height))
    cv2.rectangle(image, (left, top), (right, bottom), color, line_width)
    _put_label(image, label or f'R{index}', left + 4, max(18, top - 6), color)


def _draw_point(
    image: np.ndarray,
    mark: PointMark,
    index: int,
    color: tuple[int, int, int],
    point_size: int,
) -> None:
    label, (rx, ry) = mark
    height, width = image.shape[:2]
    x, y = _pixel_position(width, height, rx, ry)
    half = point_size // 2
    left, top = max(0, x - half), max(0, y - half)
    right, bottom = min(width, left + point_size), min(height, top + point_size)
    image[top:bottom, left:right] = color
    _put_label(image, label or f'P{index}', min(width - 1, x + 6), max(18, y - 6), color)


def annotate_image(
    image: np.ndarray,
    rois: Sequence[RoiMark],
    points: Sequence[PointMark],
    *,
    point_size: int = 2,
    line_width: int = 2,
) -> np.ndarray:
    """Return a copy of ``image`` with ROI rectangles and pixel markers."""
    if point_size not in {1, 2, 3}:
        raise ValueError('point_size must be 1, 2, or 3')
    if line_width <= 0:
        raise ValueError('line_width must be positive')

    marked = image.copy()
    for index, mark in enumerate(rois, 1):
        _draw_roi(marked, mark, index, ROI_COLORS[(index - 1) % len(ROI_COLORS)], line_width)
    for index, mark in enumerate(points, 1):
        _draw_point(
            marked,
            mark,
            index,
            POINT_COLORS[(index - 1) % len(POINT_COLORS)],
            point_size,
        )
    return marked


def _default_output(image_path: Path | None) -> Path:
    if image_path is not None:
        return RESULT_ROOT / f'{image_path.stem}_annotated.png'
    return RESULT_ROOT / f'annotated_{datetime.now(UTC):%Y%m%d_%H%M%S}.png'


def _print_summary(
    image: np.ndarray,
    rois: Sequence[RoiMark],
    points: Sequence[PointMark],
) -> None:
    height, width = image.shape[:2]
    print(f'image: {width}x{height}')
    for index, (label, (x1, y1, x2, y2)) in enumerate(rois, 1):
        left, top = int(x1 * width), int(y1 * height)
        right, bottom = int(x2 * width), int(y2 * height)
        print(
            f'ROI {label or f"R{index}"}: '
            f'normalized=({x1:.4f},{y1:.4f},{x2:.4f},{y2:.4f}) '
            f'pixels=[{left}:{right}, {top}:{bottom})'
        )
    for index, (label, (x, y)) in enumerate(points, 1):
        px, py = _pixel_position(width, height, x, y)
        print(f'POINT {label or f"P{index}"}: normalized=({x:.4f},{y:.4f}) pixels=({px},{py})')


def add_arguments(parser: argparse.ArgumentParser) -> None:
    source = parser.add_mutually_exclusive_group()
    source.add_argument('-i', '--image', type=Path, help='source image; omit to capture from ADB')
    source.add_argument('--serial', help='ADB serial used when --image is omitted')
    parser.add_argument('--adb-path', type=Path, help='override the bundled adb.exe')
    parser.add_argument(
        '--roi',
        action='append',
        default=[],
        type=_parse_labeled_roi,
        metavar='[LABEL:]X1,Y1,X2,Y2',
        help='normalized ROI; repeat for multiple rectangles',
    )
    parser.add_argument(
        '--point',
        action='append',
        default=[],
        type=_parse_labeled_point,
        metavar='[LABEL:]X,Y',
        help='normalized pixel probe; repeat for multiple points',
    )
    parser.add_argument(
        '--point-size',
        type=_parse_point_size,
        default=2,
        help='marker side length in pixels (1-3, default: 2)',
    )
    parser.add_argument(
        '--line-width',
        type=_parse_line_width,
        default=2,
        help='ROI outline width in pixels (default: 2)',
    )
    parser.add_argument('-o', '--output', type=Path, help='output PNG; defaults to result/annotate')


def run(args: argparse.Namespace) -> int:
    if not args.roi and not args.point:
        raise CropToolError('at least one --roi or --point is required')
    image = _load_source(args)
    marked = annotate_image(
        image,
        args.roi,
        args.point,
        point_size=args.point_size,
        line_width=args.line_width,
    )
    output = args.output or _default_output(args.image)
    _write_png(output, marked)
    _print_summary(image, args.roi, args.point)
    print(f'output: {output}')
    return 0
