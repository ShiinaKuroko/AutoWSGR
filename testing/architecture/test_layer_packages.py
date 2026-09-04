"""Regression checks for the five-package architecture boundary."""

from __future__ import annotations

import ast
from pathlib import Path


_ROOT = Path(__file__).parents[2] / 'autowsgr'
_LAYERS = ('server', 'dispatch', 'business', 'application', 'common')
_RANK = {name: index for index, name in enumerate(_LAYERS)}


def test_application_and_common_packages_import_without_side_effects() -> None:
    import autowsgr.application
    import autowsgr.common

    assert autowsgr.application.__doc__
    assert autowsgr.common.__doc__


def test_autowsgr_has_only_the_five_architecture_packages() -> None:
    packages = {
        item.name for item in _ROOT.iterdir() if item.is_dir() and item.name != '__pycache__'
    }

    assert packages == set(_LAYERS)


def test_layer_imports_only_point_downward() -> None:
    violations: list[str] = []

    for path in _ROOT.rglob('*.py'):
        if '__pycache__' in path.parts:
            continue
        owner = path.relative_to(_ROOT).parts[0]
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        imported_layers: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or '']
            else:
                continue
            for name in names:
                parts = name.split('.')
                if len(parts) > 1 and parts[0] == 'autowsgr' and parts[1] in _RANK:
                    imported_layers.add(parts[1])
        violations.extend(
            f'{path}: {owner} -> {target}'
            for target in imported_layers
            if _RANK[target] < _RANK[owner]
        )

    assert violations == []
