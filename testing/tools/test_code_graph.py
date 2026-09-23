"""Checks for the repository Code Graph builder."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from tools.code_graph.code_graph import (
    GraphConfig,
    LayerRule,
    build_graph,
    check_graph,
    main,
)


if TYPE_CHECKING:
    from pathlib import Path


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def _fixture_config() -> GraphConfig:
    return GraphConfig(
        repository='fixture',
        roots=('pkg', 'testing'),
        exclude=(),
        layers=(),
    )


def test_build_collects_static_and_declared_relationships(tmp_path: Path) -> None:
    _write(tmp_path, 'pkg/__init__.py', "__all__ = ['run']\nfrom pkg.a import run\n")
    _write(
        tmp_path,
        'pkg/a.py',
        """from importlib import import_module
from pkg.b import Widget
import pkg.c as c

PLAN = 'data/plan.yaml'

@router.get('/health')
def run() -> Widget:
    value = Widget()
    import_module('pkg.b')
    return c.helper(value)
""",
    )
    _write(tmp_path, 'pkg/b.py', 'class Widget:\n    pass\n')
    _write(tmp_path, 'pkg/c.py', 'def helper(value: object) -> object:\n    return value\n')
    _write(tmp_path, 'testing/test_a.py', 'from pkg.a import run\nrun()\n')

    graph = build_graph(tmp_path, _fixture_config())

    assert check_graph(graph) == []
    assert any(node['id'].endswith('pkg/b.py::Widget') for node in graph['nodes'])
    assert any(node['type'] == 'route' for node in graph['nodes'])
    assert any(edge['type'] == 'exports' for edge in graph['edges'])
    assert any(edge['type'] == 'constructs' for edge in graph['edges'])
    assert any(edge['type'] == 'calls' for edge in graph['edges'])
    assert any(edge['type'] == 'declared_dynamic' for edge in graph['edges'])
    assert any(edge['type'] == 'uses_resource' for edge in graph['edges'])
    assert any(edge['type'] == 'tests' for edge in graph['edges'])

    assert graph == build_graph(tmp_path, _fixture_config())


def test_check_reports_forbidden_layer_import(tmp_path: Path) -> None:
    _write(tmp_path, 'app/a.py', 'from common.b import value\n')
    _write(tmp_path, 'common/b.py', 'from app.a import value\n')
    config = GraphConfig(
        repository='fixture',
        roots=('app', 'common'),
        exclude=(),
        layers=(
            LayerRule('app', 'app', ('common',)),
            LayerRule('common', 'common', ()),
        ),
    )

    violations = check_graph(build_graph(tmp_path, config))

    assert any('forbidden layer import: common -> app' in item for item in violations)


def test_cli_build_check_explain_and_diff(tmp_path: Path, capsys: object) -> None:
    _write(
        tmp_path,
        'pyproject.toml',
        """[tool.autowsgr-code-graph]
repository = 'fixture'
roots = ['pkg']
exclude = []
""",
    )
    _write(tmp_path, 'pkg/a.py', 'def run() -> None:\n    return None\n')
    output = tmp_path / 'graph.json'

    assert main(['build', '--root', str(tmp_path), '--output', str(output)]) == 0
    assert main(['check', '--graph', str(output)]) == 0
    assert main(['explain', 'pkg.a', '--graph', str(output)]) == 0
    assert json.loads(output.read_text(encoding='utf-8'))['schema_version'] == 1

    _write(tmp_path, 'pkg/b.py', 'def added() -> None:\n    return None\n')
    changed = build_graph(tmp_path, GraphConfig.from_project(tmp_path))
    changed_path = tmp_path / 'changed.json'
    changed_path.write_text(json.dumps(changed), encoding='utf-8')
    assert main(['diff', str(output), str(changed_path)]) == 0
    assert 'pkg/b.py' in capsys.readouterr().out


def test_build_rejects_dirty_snapshot_when_requested(tmp_path: Path) -> None:
    _write(tmp_path, 'pkg/a.py', 'value = 1\n')
    config = _fixture_config()

    with pytest.raises(ValueError, match='baseline requires a clean worktree'):
        build_graph(tmp_path, config, require_clean=True)
