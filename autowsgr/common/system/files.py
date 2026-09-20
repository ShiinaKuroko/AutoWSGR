"""通用文件边界。

提供 YAML 映射和图像文件的安全读取，以及 YAML 映射的原子写入。
下层依赖：Python 标准库、YAML 解析库和图像解码库。
边界：只处理路径、编码、解析和写入机制，不解释文件中的业务字段。
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml


if TYPE_CHECKING:
    import numpy as np


def _resolve_path(path: str | Path, allowed_root: str | Path) -> Path:
    """规范化路径，并确认目标仍位于允许根目录内。

    Args:
        path: 待访问的文件路径。
        allowed_root: 允许访问的根目录。

    Returns:
        规范化后的绝对路径。

    Raises:
        ValueError: 目标路径超出允许根目录。
    """
    target = Path(path).expanduser().resolve()
    root = Path(allowed_root).expanduser().resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError(f'路径超出允许目录: {target}') from None
    return target


def load_yaml(path: str | Path, *, allowed_root: str | Path) -> dict[str, Any]:
    """读取允许目录内的 YAML 映射。

    Args:
        path: YAML 文件路径。
        allowed_root: 规范化后必须包含 `path` 的允许根目录。

    Returns:
        解析后的映射；空文件返回空映射。

    Raises:
        FileNotFoundError: 文件不存在。
    """
    # 先完成路径校验，再执行任何文件读取。
    target = _resolve_path(path, allowed_root)
    if not target.exists():
        raise FileNotFoundError(f'YAML 文件不存在: {target}')
    with target.open(encoding='utf-8') as stream:
        return yaml.safe_load(stream) or {}


def load_image(path: str | Path, *, allowed_root: str | Path) -> np.ndarray:
    """读取允许目录内的图像，并转换为 RGB 数组。

    Args:
        path: 图像文件路径。
        allowed_root: 规范化后必须包含 `path` 的允许根目录。

    Returns:
        RGB 顺序的图像数组。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: 文件无法解码为图像。
    """
    target = _resolve_path(path, allowed_root)
    if not target.is_file():
        raise FileNotFoundError(f'图像文件不存在: {target}')

    import cv2
    import numpy as np

    encoded = np.fromfile(target, dtype=np.uint8)
    bgr = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f'无法解码图像文件: {target}')
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def save_yaml(data: dict[str, Any], path: str | Path, *, allowed_root: str | Path) -> None:
    """将 YAML 映射原子写入允许目录内的文件。

    Args:
        data: 已完成业务校验的 YAML 映射。
        path: 目标文件路径；父目录不存在时按需创建。
        allowed_root: 规范化后必须包含目标路径的允许根目录。
    """
    # 1. 先校验目标路径，避免写入允许范围之外的文件。
    target = _resolve_path(path, allowed_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        # 2. 先在目标目录写临时文件，避免直接覆盖现有用户数据。
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=target.parent,
            prefix=f'.{target.name}.',
            suffix='.tmp',
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            yaml.dump(
                data,
                stream,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
            stream.flush()
            os.fsync(stream.fileno())
        # 3. 临时文件完整写入后再替换目标文件。
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def save_image(image: np.ndarray, path: str | Path, *, allowed_root: str | Path) -> None:
    """将 RGB 图像原子写入允许目录内的 PNG 文件。

    Args:
        image: RGB 顺序的图像数组。
        path: PNG 文件路径。
        allowed_root: 规范化后必须包含目标路径的允许根目录。

    Raises:
        ValueError: 图像无法编码为 PNG。
    """
    target = _resolve_path(path, allowed_root)
    target.parent.mkdir(parents=True, exist_ok=True)

    import cv2

    source = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    encoded, data = cv2.imencode('.png', source)
    if not encoded:
        raise ValueError(f'无法编码图像文件: {target}')

    temporary = target.with_name(f'.{target.name}.tmp')
    try:
        temporary.write_bytes(data.tobytes())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


__all__ = ['load_image', 'load_yaml', 'save_image', 'save_yaml']
