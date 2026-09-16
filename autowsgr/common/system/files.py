"""通用文件边界。

当前提供 YAML 映射的安全读取和原子写入；其他通用文件格式按相同契约扩展。
下层依赖：Python 标准库和 YAML 解析库。
边界：只处理路径、编码、解析和写入机制，不解释文件中的业务字段。
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


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


__all__ = ['load_yaml', 'save_yaml']
