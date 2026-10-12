"""模块功能：通用文件边界。

提供 YAML 映射的安全读取与原子写入，以及图像文件的读取与保存。

上层调用：
- application.ui.navigation.checker.calibration：读写识别校准 YAML。
- dispatch.processor：读写任务数据 YAML。
- common.vision 和 common.device：保存模板与截图图像。

下层依赖：
- Python 标准库 os、tempfile 和 pathlib。
- YAML 解析库：解析和序列化 YAML 映射。
- NumPy 和 OpenCV：仅在图像能力内按需加载，不作为静态依赖。

边界：只处理路径、编码、解析和写入机制，不解释文件中的业务字段。
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml


if TYPE_CHECKING:
    import numpy


def load_yaml(path: str | Path, *, allowed_root: str | Path) -> dict[str, Any]:
    """读取允许目录内的 YAML 映射。

    Args:
        path: YAML 文件路径。
        allowed_root: 规范化后必须包含 path 的允许根目录。

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


def load_image(path: str | Path, *, allowed_root: str | Path) -> numpy.ndarray:
    """读取允许目录内的图像，并转换为 RGB 数组。

    Args:
        path: 图像文件路径。
        allowed_root: 规范化后必须包含 path 的允许根目录。

    Returns:
        RGB 顺序的图像数组。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: 文件无法解码为图像。
    """
    target = _resolve_path(path, allowed_root)
    if not target.is_file():
        raise FileNotFoundError(f'图像文件不存在: {target}')

    # system 层不静态依赖图像库，这里按需加载 OpenCV 和 NumPy。
    import cv2
    import numpy

    encoded = numpy.fromfile(target, dtype=numpy.uint8)
    bgr_image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if bgr_image is None:
        raise ValueError(f'无法解码图像文件: {target}')
    return cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)


def save_yaml(yaml_mapping: dict[str, Any], path: str | Path, *, allowed_root: str | Path) -> None:
    """将 YAML 映射原子写入允许目录内的文件。

    Args:
        yaml_mapping: 已完成业务校验的 YAML 映射。
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
                yaml_mapping,
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


def save_image(image: numpy.ndarray, path: str | Path, *, allowed_root: str | Path) -> None:
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

    # system 层不静态依赖图像库，这里按需加载 OpenCV。
    import cv2

    bgr_image = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    encoded, png_bytes = cv2.imencode('.png', bgr_image)
    if not encoded:
        raise ValueError(f'无法编码图像文件: {target}')

    temporary_path = target.with_name(f'.{target.name}.tmp')
    try:
        temporary_path.write_bytes(png_bytes.tobytes())
        os.replace(temporary_path, target)
    finally:
        temporary_path.unlink(missing_ok=True)


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


__all__ = ['load_image', 'load_yaml', 'save_image', 'save_yaml']
