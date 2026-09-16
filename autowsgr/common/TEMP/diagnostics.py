"""Temporary diagnostic and image-artifact helpers."""

from __future__ import annotations

import inspect
import time as _time
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
from loguru import logger


if TYPE_CHECKING:
    import numpy as np


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_image_dir: Path | None = None


def caller_info(depth: int = 1) -> str:
    """Return the caller's project-relative path, line, and function."""
    try:
        frame = inspect.stack()[depth + 1]
        filepath = Path(frame.filename)
        try:
            relative = filepath.relative_to(_PROJECT_ROOT).as_posix()
        except ValueError:
            relative = filepath.name
    except Exception:
        return '<unknown>'
    return f'{relative}:{frame.lineno} in {frame.function}'


def save_image(
    image: np.ndarray,
    tag: str = 'screenshot',
    img_dir: Path | None = None,
) -> Path | None:
    """Save an RGB screenshot for diagnostics when an artifact directory is supplied."""
    target_dir = img_dir or _image_dir
    if target_dir is None:
        return None

    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _time.strftime('%H%M%S') + f'_{int(_time.monotonic() * 1000) % 1000:03d}'
    path = target_dir / f'{tag}_{timestamp}.png'
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    ok, buffer = cv2.imencode('.png', bgr)
    if not ok:
        logger.warning('截图保存失败: {}', path)
        return None
    path.write_bytes(buffer.tobytes())
    logger.debug('截图已保存: {}', path)
    return path


__all__ = ['caller_info', 'save_image']
