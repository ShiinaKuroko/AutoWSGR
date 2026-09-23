"""战斗计划资源路径解析。"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _get_package_data_dir() -> Path:
    """获取 ``autowsgr`` 包安装目录下的资源目录。"""
    spec = importlib.util.find_spec('autowsgr')
    if spec is None or spec.origin is None:
        raise RuntimeError('无法定位 autowsgr 包安装路径')
    return Path(spec.origin).resolve().parent / 'common' / 'data'


def _plan_candidates(directory: Path, name: str) -> list[Path]:
    """返回策略文件候选路径。"""
    base = directory / name
    if base.suffix:
        return [base]
    return [base, base.with_suffix('.yaml')]


def resolve_plan_path(
    name_or_path: str | Path,
    category: str = 'normal_fight',
    plan_root: str | Path | None = None,
) -> Path:
    """按用户目录优先级解析战斗计划路径。"""
    path = Path(name_or_path)
    searched: list[Path] = []

    if path.exists():
        return path.resolve()
    searched.append(path)

    if not path.suffix:
        with_suffix = path.with_suffix('.yaml')
        if with_suffix.exists():
            return with_suffix.resolve()
        searched.append(with_suffix)

    if plan_root is not None:
        for candidate in _plan_candidates(Path(plan_root) / category, path.name):
            if candidate.exists():
                return candidate.resolve()
            searched.append(candidate)

    data_dir = _get_package_data_dir() / 'plan' / category
    for candidate in _plan_candidates(data_dir, path.name):
        if candidate.exists():
            return candidate.resolve()
        searched.append(candidate)

    raise FileNotFoundError(
        f'策略文件未找到: {name_or_path!r}\n已搜索: {" | ".join(str(item) for item in searched)}',
    )
