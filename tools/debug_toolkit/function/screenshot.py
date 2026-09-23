"""保存 ADB 截图和 debug 过程中的图片产物。"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import cv2

from autowsgr.common.device import adb

from tools.debug_toolkit.function.collect import (
    _read_saved_serial,
    _write_png,
)


if TYPE_CHECKING:
    import argparse

    import numpy as np


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = PACKAGE_ROOT / 'result' / 'screenshot'


def save_image(
    image: np.ndarray,
    tag: str = 'screenshot',
    img_dir: Path | None = None,
) -> Path | None:
    """保存 RGB 图片；未提供产物目录时跳过保存。

    Args:
        image: RGB 排列的截图数组。
        tag: 输出文件名前缀。
        img_dir: 图片产物目录。

    Returns:
        已保存的图片路径；未提供目录时返回 None。
    """
    if img_dir is None:
        return None

    img_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime('%H%M%S') + f'_{int(time.monotonic() * 1000) % 1000:03d}'
    path = img_dir / f'{tag}_{timestamp}.png'
    success, encoded = cv2.imencode('.png', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if not success:
        return None
    encoded.tofile(str(path))
    return path


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--serial', help='ADB serial, defaults to the saved serial')
    parser.add_argument('--adb-path', type=Path, help='override the bundled adb.exe')
    parser.add_argument('-o', '--output', type=Path, help='explicit PNG path')


def run(args: argparse.Namespace) -> int:
    adb_path = adb.find_adb(args.adb_path)
    serial = args.serial or _read_saved_serial()
    image = adb.capture_screen(serial, adb_path)
    output = args.output or RESULT_ROOT / f'screenshot_{datetime.now(UTC):%Y%m%d_%H%M%S}.png'
    _write_png(output, image)
    print(output)
    return 0
