"""Build and inspect a deterministic static graph of the AutoWSGR repository."""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path


SCHEMA_VERSION = 1
DEFAULT_OUTPUT = Path('.tmp/code-graph/graph.json')
EDGE_TYPES = frozenset(
    {
        'imports',
        'exports',
        'calls',
        'constructs',
        'registers',
        'loads_config',
        'uses_resource',
        'tests',
        'declared_dynamic',
    }
)
RESOURCE_SUFFIXES = frozenset(
    {
        '.json',
        '.onnx',
        '.png',
        '.toml',
        '.txt',
        '.yaml',
        '.yml',
    }
)
ROUTE_METHODS = frozenset({'delete', 'get', 'patch', 'post', 'put', 'websocket'})
REGISTRATION_NAMES = frozenset({'register', 'register_executor', 'register_page', 'register_task'})
CONFIG_LOAD_NAMES = frozenset({'from_yaml', 'load_config', 'load_yaml', 'read_yaml'})


@dataclass(frozen=True)
class LayerRule:
    """Describe which project layers a layer may import."""

    name: str
    path: str
    allows: tuple[str, ...]


@dataclass(frozen=True)
class GraphConfig:
    """Configuration needed to build a graph without repository-specific code."""

    repository: str
    roots: tuple[str, ...]
    exclude: tuple[str, ...]
    layers: tuple[LayerRule, ...]
    dynamic_edges: tuple[dict[str, object], ...] = ()

    @classmethod
    def from_project(cls, project_root: Path) -> GraphConfig:
        defaults = cls(
            repository='autowsgr',
            roots=('autowsgr', 'testing', 'tools', 'examples'),
            exclude=('.git', '.venv', 'build', 'dist', '__pycache__', '.pytest_tmp', '.tmp'),
            layers=(),
        )
        pyproject = project_root / 'pyproject.toml'
        if not pyproject.is_file():
            return defaults

        with pyproject.open('rb') as stream:
            document = tomllib.load(stream)
        tool = document.get('tool', {}).get('autowsgr-code-graph', {})
        if not isinstance(tool, Mapping):
            return defaults

        project = document.get('project', {})
        project_name = project.get('name') if isinstance(project, Mapping) else None
        repository = str(tool.get('repository') or project_name or project_root.name)
        roots = _string_tuple(tool.get('roots'), defaults.roots)
        exclude = _string_tuple(tool.get('exclude'), defaults.exclude)
        layers = tuple(
            LayerRule(
                name=str(item.get('name', '')),
                path=str(item.get('path', '')),
                allows=tuple(str(value) for value in item.get('allows', ())),
            )
            for item in tool.get('layers', ())
            if isinstance(item, Mapping) and item.get('name') and item.get('path')
        )
        dynamic_edges = tuple(
            dict(item) for item in tool.get('dynamic_edges', ()) if isinstance(item, Mapping)
        )
        return cls(repository, roots, exclude, layers, dynamic_edges)

    def as_dict(self) -> dict[str, object]:
        """Return the stable configuration representation stored in graph JSON."""
        return {
            'repository': self.repository,
            'roots': list(self.roots),
            'exclude': list(self.exclude),
            'layers': [
                {'name': rule.name, 'path': rule.path, 'allows': list(rule.allows)}
                for rule in self.layers
            ],
            'dynamic_edges': list(self.dynamic_edges),
        }


def _string_tuple(value: object, default: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return default
    return tuple(str(item) for item in value)


def _git_text(project_root: Path, *arguments: str) -> str:
    git = shutil.which('git')
    if git is None:
        return ''
    result = subprocess.run(  # noqa: S603
        [git, '-C', str(project_root), *arguments],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode:
        return ''
    return result.stdout.strip()


def _source_snapshot(project_root: Path) -> dict[str, object]:
    revision = _git_text(project_root, 'rev-parse', 'HEAD') or 'unknown'
    status = _git_text(project_root, 'status', '--short', '--untracked-files=all')
    dirty_files = sorted(line for line in status.splitlines() if line)
    return {'revision': revision, 'dirty': bool(dirty_files), 'dirty_files': dirty_files}


def _relative_path(path: Path, project_root: Path) -> str:
    return path.relative_to(project_root).as_posix()


def _module_name(relative_path: str) -> str:
    parts = list(Path(relative_path).with_suffix('').parts)
    if parts and parts[-1] == '__init__':
        parts.pop()
    return '.'.join(parts)


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f'{parent}.{node.attr}' if parent else node.attr
    return None


def _string_value(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_resource(value: str) -> bool:
    normalized = value.replace('\\', '/').split('?', 1)[0].lower()
    return any(normalized.endswith(suffix) for suffix in RESOURCE_SUFFIXES)


def _path_matches(path: str, prefix: str) -> bool:
    normalized = prefix.replace('\\', '/').rstrip('/')
    return path == normalized or path.startswith(normalized + '/')


class _GraphBuilder:
    def __init__(self, project_root: Path, config: GraphConfig) -> None:
        self.project_root = project_root
        self.config = config
        self.files = self._discover_files()
        self.nodes: dict[str, dict[str, object]] = {}
        self.edges: dict[tuple[str, str, str, str, int], dict[str, object]] = {}
        self.unresolved: list[dict[str, object]] = []
        self.trees: dict[str, ast.Module] = {}
        self.paths: dict[str, str] = {}
        self.module_ids: dict[str, str] = {}
        self.module_names: dict[str, str] = {}
        self.symbol_ids: dict[tuple[str, str], str] = {}
        self.symbol_kinds: dict[str, str] = {}
        self.imports: dict[str, dict[str, str]] = {}

    def build(self, source: dict[str, object]) -> dict[str, object]:
        self._collect_modules()
        self._collect_definitions()
        self._collect_imports()
        self._collect_exports()
        self._collect_relationships()
        self._collect_declared_edges()
        return {
            'schema_version': SCHEMA_VERSION,
            'source': source,
            'config': self.config.as_dict(),
            'nodes': sorted(self.nodes.values(), key=lambda node: str(node['id'])),
            'edges': sorted(
                self.edges.values(),
                key=lambda edge: (
                    str(edge['type']),
                    str(edge['source']),
                    str(edge['target']),
                    int(edge['line']),
                    str(edge['path']),
                ),
            ),
            'unresolved': sorted(
                self.unresolved,
                key=lambda item: (
                    str(item.get('kind')),
                    str(item.get('path')),
                    int(item.get('line', 0)),
                    str(item.get('value')),
                ),
            ),
        }

    def _discover_files(self) -> tuple[Path, ...]:
        files: list[Path] = []
        for root_name in self.config.roots:
            root = self.project_root / root_name
            if not root.is_dir():
                continue
            files.extend(
                path
                for path in root.rglob('*.py')
                if not any(
                    part in self.config.exclude
                    for part in path.relative_to(self.project_root).parts
                )
            )
        return tuple(sorted(set(files)))

    def _module_id(self, relative_path: str) -> str:
        return f'{self.config.repository}:{relative_path}'

    def _symbol_id(self, module_name: str, qualified_name: str) -> str:
        module_id = self.module_ids[module_name]
        return f'{module_id}::{qualified_name}'

    def _node(
        self,
        node_id: str,
        node_type: str,
        name: str,
        path: str,
        line: int,
        qualified_name: str | None = None,
    ) -> None:
        node: dict[str, object] = {
            'id': node_id,
            'type': node_type,
            'name': name,
            'path': path,
            'line': line,
            'layer': self._layer(path),
            'public': not name.startswith('_'),
        }
        if qualified_name is not None:
            node['qualified_name'] = qualified_name
        self.nodes[node_id] = node

    def _layer(self, path: str) -> str | None:
        matches = (rule for rule in self.config.layers if _path_matches(path, rule.path))
        rule = max(matches, key=lambda item: len(item.path), default=None)
        return rule.name if rule else None

    def _collect_modules(self) -> None:
        for path in self.files:
            relative_path = _relative_path(path, self.project_root)
            module_name = _module_name(relative_path)
            module_id = self._module_id(relative_path)
            if module_name not in self.module_ids or path.name == '__init__.py':
                self.module_ids[module_name] = module_id
                self.module_names[module_id] = module_name
            self.paths[module_id] = relative_path
            try:
                tree = ast.parse(path.read_text(encoding='utf-8'), filename=relative_path)
            except (OSError, SyntaxError) as exc:
                self.unresolved.append(
                    {
                        'kind': 'parse_error',
                        'path': relative_path,
                        'line': getattr(exc, 'lineno', 0) or 0,
                        'value': str(exc),
                    }
                )
                continue
            self.trees[module_name] = tree
            self._node(
                module_id,
                'package' if path.name == '__init__.py' else 'module',
                module_name,
                relative_path,
                1,
                module_name,
            )

    def _collect_definitions(self) -> None:
        for module_name, tree in self.trees.items():
            self._visit_definitions(module_name, tree.body)

    def _visit_definitions(
        self,
        module_name: str,
        body: list[ast.stmt],
        prefix: str = '',
        class_prefix: str | None = None,
    ) -> None:
        for node in body:
            if not isinstance(node, (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef)):
                continue
            qualified_name = f'{prefix}.{node.name}' if prefix else node.name
            node_type = (
                'class'
                if isinstance(node, ast.ClassDef)
                else 'method'
                if class_prefix
                else 'function'
            )
            symbol_id = self._symbol_id(module_name, qualified_name)
            self.symbol_ids[(module_name, qualified_name)] = symbol_id
            self.symbol_kinds[symbol_id] = node_type
            self._node(
                symbol_id,
                node_type,
                node.name,
                self.paths[self.module_ids[module_name]],
                node.lineno,
                f'{module_name}.{qualified_name}',
            )
            if isinstance(node, ast.ClassDef):
                self._visit_definitions(module_name, node.body, qualified_name, qualified_name)
            else:
                self._visit_definitions(module_name, node.body, qualified_name, class_prefix)
            self._collect_decorators(module_name, symbol_id, node)

    def _collect_decorators(self, module_name: str, source_id: str, node: ast.AST) -> None:
        decorators = getattr(node, 'decorator_list', ())
        for decorator in decorators:
            if not isinstance(decorator, ast.Call):
                continue
            method = _dotted_name(decorator.func)
            if not method or method.rsplit('.', 1)[-1] not in ROUTE_METHODS:
                continue
            path = _string_value(decorator.args[0] if decorator.args else None)
            if path is None:
                self.unresolved.append(
                    {
                        'kind': 'dynamic_route',
                        'path': self.paths[self.module_ids[module_name]],
                        'line': decorator.lineno,
                        'value': method,
                    }
                )
                continue
            http_method = method.rsplit('.', 1)[-1].upper()
            route_id = f'{self.config.repository}:route:{http_method} {path}'
            route_path = self.paths[self.module_ids[module_name]]
            self._node(route_id, 'route', f'{http_method} {path}', route_path, decorator.lineno)
            self._edge(
                source_id,
                route_id,
                'registers',
                route_path,
                decorator.lineno,
                confidence='static',
            )

    def _relative_base(self, module_name: str, level: int, is_package: bool) -> str:
        parts = module_name.split('.')
        if not is_package:
            parts = parts[:-1]
        keep = max(0, len(parts) - level + 1)
        return '.'.join(parts[:keep])

    def _module_target(self, name: str) -> str | None:
        parts = name.split('.')
        for index in range(len(parts), 0, -1):
            candidate = '.'.join(parts[:index])
            if candidate in self.module_ids:
                return self.module_ids[candidate]
        return None

    def _from_target(
        self,
        module_name: str,
        imported_module: str,
        imported_name: str,
        level: int,
        is_package: bool,
    ) -> str | None:
        base = self._relative_base(module_name, level, is_package) if level else ''
        parent_name = '.'.join(part for part in (base, imported_module) if part)
        if (target := self.symbol_ids.get((parent_name, imported_name))) is not None:
            return target
        if (
            target := self.module_ids.get(
                '.'.join(part for part in (parent_name, imported_name) if part)
            )
        ) is not None:
            return target
        if (target := self.module_ids.get(parent_name)) is not None:
            return target
        if (target := self.module_ids.get(base)) is not None:
            return target
        return None

    def _collect_imports(self) -> None:
        for module_name, tree in self.trees.items():
            module_id = self.module_ids[module_name]
            relative_path = self.paths[module_id]
            is_package = Path(relative_path).name == '__init__.py'
            aliases: dict[str, str] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = self._module_target(alias.name)
                        if target is None:
                            continue
                        bound_name = alias.asname or alias.name.split('.')[0]
                        bound_target = (
                            self._module_target(alias.name.split('.')[0])
                            if alias.asname is None
                            else target
                        )
                        aliases[bound_name] = bound_target or target
                        self._import_edge(module_id, target, relative_path, node.lineno)
                elif isinstance(node, ast.ImportFrom):
                    imported_module = node.module or ''
                    for alias in node.names:
                        if alias.name == '*':
                            continue
                        target = self._from_target(
                            module_name,
                            imported_module,
                            alias.name,
                            node.level,
                            is_package,
                        )
                        if target is None:
                            continue
                        aliases[alias.asname or alias.name] = target
                        self._import_edge(module_id, target, relative_path, node.lineno)
            self.imports[module_name] = aliases

    def _import_edge(self, source_id: str, target_id: str, path: str, line: int) -> None:
        self._edge(source_id, target_id, 'imports', path, line)
        if path.startswith('testing/'):
            self._edge(source_id, target_id, 'tests', path, line)

    def _collect_exports(self) -> None:
        for module_name, tree in self.trees.items():
            module_id = self.module_ids[module_name]
            for node in tree.body:
                if not isinstance(node, ast.Assign):
                    continue
                if not any(
                    isinstance(target, ast.Name) and target.id == '__all__'
                    for target in node.targets
                ):
                    continue
                values = (
                    node.value.elts
                    if isinstance(node.value, (ast.List, ast.Set, ast.Tuple))
                    else ()
                )
                for value in values:
                    name = _string_value(value)
                    if name is None:
                        continue
                    target = self.symbol_ids.get((module_name, name)) or self.imports.get(
                        module_name, {}
                    ).get(name)
                    if target is None:
                        self.unresolved.append(
                            {
                                'kind': 'export',
                                'path': self.paths[module_id],
                                'line': node.lineno,
                                'value': name,
                            }
                        )
                        continue
                    self._edge(module_id, target, 'exports', self.paths[module_id], node.lineno)

    def _collect_relationships(self) -> None:
        for module_name, tree in self.trees.items():
            visitor = _RelationshipVisitor(self, module_name)
            visitor.visit(tree)

    def _collect_declared_edges(self) -> None:
        for item in self.config.dynamic_edges:
            source = str(item.get('source', ''))
            target = str(item.get('target', ''))
            kind = str(item.get('type', 'declared_dynamic'))
            path = str(item.get('path', 'pyproject.toml'))
            line = int(item.get('line', 0) or 0)
            if kind not in EDGE_TYPES:
                self.unresolved.append(
                    {'kind': 'invalid_declared_edge', 'path': path, 'line': line, 'value': kind}
                )
                continue
            if source not in self.nodes or target not in self.nodes:
                self.unresolved.append(
                    {
                        'kind': 'missing_declared_edge_endpoint',
                        'path': path,
                        'line': line,
                        'value': f'{source} -> {target}',
                    }
                )
                continue
            self._edge(
                source,
                target,
                kind,
                path,
                line,
                confidence='declared',
                evidence=str(item.get('reason', '')),
            )

    def _resolve_expression(
        self,
        module_name: str,
        node: ast.AST,
        class_stack: tuple[str, ...],
    ) -> str | None:
        aliases = self.imports.get(module_name, {})
        target: str | None = None
        if isinstance(node, ast.Name):
            target = aliases.get(node.id)
            if target is None:
                for class_name in reversed(class_stack):
                    target = self.symbol_ids.get((module_name, f'{class_name}.{node.id}'))
                    if target is not None:
                        break
            if target is None:
                target = self.symbol_ids.get((module_name, node.id))
        elif isinstance(node, ast.Attribute):
            if (
                isinstance(node.value, ast.Name)
                and node.value.id in {'self', 'cls'}
                and class_stack
            ):
                target = self.symbol_ids.get((module_name, f'{class_stack[-1]}.{node.attr}'))
            else:
                base = self._resolve_expression(module_name, node.value, class_stack)
                if base is not None:
                    if base in self.module_names:
                        base_module = self.module_names[base]
                        target = self.symbol_ids.get(
                            (base_module, node.attr)
                        ) or self.module_ids.get(f'{base_module}.{node.attr}')
                    else:
                        target = self.symbol_ids.get((module_name, f'{base}.{node.attr}'))
        return target

    def _resource_node(self, value: str, path: str, line: int) -> str:
        normalized = value.replace('\\', '/')
        node_id = f'{self.config.repository}:resource:{normalized}'
        self._node(node_id, 'resource', normalized, path, line)
        return node_id

    def _registry_node(self, kind: str, value: str, path: str, line: int) -> str:
        node_id = f'{self.config.repository}:registry:{kind}:{value}'
        self._node(node_id, 'registry', f'{kind}:{value}', path, line)
        return node_id

    def _edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        path: str,
        line: int,
        *,
        confidence: str = 'static',
        evidence: str | None = None,
    ) -> None:
        if source_id not in self.nodes or target_id not in self.nodes:
            return
        edge: dict[str, object] = {
            'source': source_id,
            'target': target_id,
            'type': edge_type,
            'path': path,
            'line': line,
            'confidence': confidence,
        }
        if evidence:
            edge['evidence'] = evidence
        key = (edge_type, source_id, target_id, path, line)
        self.edges[key] = edge


class _RelationshipVisitor(ast.NodeVisitor):
    def __init__(self, builder: _GraphBuilder, module_name: str) -> None:
        self.builder = builder
        self.module_name = module_name
        self.module_id = builder.module_ids[module_name]
        self.path = builder.paths[self.module_id]
        self.context: list[str] = [self.module_id]
        self.class_stack: list[str] = []
        self.name_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualified_name = '.'.join((*self.name_stack, node.name))
        target = self.builder.symbol_ids.get((self.module_name, qualified_name))
        self.name_stack.append(node.name)
        self.class_stack.append(qualified_name)
        if target:
            self.context.append(target)
        self.generic_visit(node)
        if target:
            self.context.pop()
        self.class_stack.pop()
        self.name_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.AsyncFunctionDef | ast.FunctionDef) -> None:
        qualified_name = '.'.join((*self.name_stack, node.name))
        target = self.builder.symbol_ids.get((self.module_name, qualified_name))
        self.name_stack.append(node.name)
        if target:
            self.context.append(target)
        self.generic_visit(node)
        if target:
            self.context.pop()
        self.name_stack.pop()

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and _is_resource(node.value):
            resource_id = self.builder._resource_node(node.value, self.path, node.lineno)
            self.builder._edge(
                self.context[-1],
                resource_id,
                'uses_resource',
                self.path,
                node.lineno,
            )

    def visit_Call(self, node: ast.Call) -> None:
        source_id = self.context[-1]
        target = self.builder._resolve_expression(
            self.module_name,
            node.func,
            tuple(self.class_stack),
        )
        if target:
            edge_type = (
                'constructs' if self.builder.symbol_kinds.get(target) == 'class' else 'calls'
            )
            self.builder._edge(source_id, target, edge_type, self.path, node.lineno)

        call_name = _dotted_name(node.func) or ''
        short_name = call_name.rsplit('.', 1)[-1]
        first_value = _string_value(node.args[0] if node.args else None)
        if short_name == 'import_module' and first_value is not None:
            target_module = self.builder._module_target(first_value)
            if target_module is None:
                self.builder.unresolved.append(
                    {
                        'kind': 'dynamic_import',
                        'path': self.path,
                        'line': node.lineno,
                        'value': first_value,
                    }
                )
            else:
                self.builder._edge(
                    source_id,
                    target_module,
                    'declared_dynamic',
                    self.path,
                    node.lineno,
                    confidence='static-dynamic',
                    evidence='importlib.import_module',
                )
        if short_name in CONFIG_LOAD_NAMES:
            for argument in node.args:
                value = _string_value(argument)
                if value is None or not _is_resource(value):
                    continue
                resource_id = self.builder._resource_node(value, self.path, node.lineno)
                self.builder._edge(
                    source_id,
                    resource_id,
                    'loads_config',
                    self.path,
                    node.lineno,
                )
        if short_name in REGISTRATION_NAMES or short_name == 'NavEdge':
            registry_value = first_value or '*'
            registry_id = self.builder._registry_node(
                short_name, registry_value, self.path, node.lineno
            )
            self.builder._edge(source_id, registry_id, 'registers', self.path, node.lineno)
        self.generic_visit(node)


def build_graph(
    project_root: Path,
    config: GraphConfig | None = None,
    *,
    require_clean: bool = False,
) -> dict[str, object]:
    """Build a graph from a repository tree."""
    root = project_root.resolve()
    graph_config = config or GraphConfig.from_project(root)
    source = _source_snapshot(root)
    if require_clean and source['dirty']:
        dirty_files = ', '.join(str(item) for item in source['dirty_files'])
        raise ValueError(f'baseline requires a clean worktree; dirty files: {dirty_files}')
    return _GraphBuilder(root, graph_config).build(source)


def write_graph(graph: Mapping[str, object], output: Path) -> None:
    """Write graph JSON with stable ordering and a trailing newline."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(graph, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )


def read_graph(path: Path) -> dict[str, object]:
    """Read one graph JSON document."""
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f'cannot read graph {path}: {exc}') from exc
    if not isinstance(document, dict):
        raise TypeError(f'graph root must be an object: {path}')
    return document


def _line_number(item: Mapping[str, object]) -> int:
    try:
        return int(item.get('line', 0) or 0)
    except (TypeError, ValueError):
        return 0


def _index_nodes(raw_nodes: list[object]) -> tuple[dict[str, Mapping[str, object]], list[str]]:
    nodes: dict[str, Mapping[str, object]] = {}
    violations: list[str] = []
    for item in raw_nodes:
        if not isinstance(item, Mapping) or not item.get('id'):
            violations.append('node is missing an id')
            continue
        node_id = str(item['id'])
        if node_id in nodes:
            violations.append(f'duplicate node: {node_id}')
        nodes[node_id] = item
    return nodes, violations


def _check_edges(
    raw_edges: list[object],
    nodes: Mapping[str, Mapping[str, object]],
) -> tuple[list[str], set[tuple[str, str, str, str, int]]]:
    violations: list[str] = []
    seen: set[tuple[str, str, str, str, int]] = set()
    for item in raw_edges:
        if not isinstance(item, Mapping):
            violations.append('edge is not an object')
            continue
        source = str(item.get('source', ''))
        target = str(item.get('target', ''))
        edge_type = str(item.get('type', ''))
        path = str(item.get('path', ''))
        line = _line_number(item)
        if source not in nodes or target not in nodes:
            violations.append(f'edge endpoint missing: {source} -> {target}')
        if edge_type not in EDGE_TYPES:
            violations.append(f'unknown edge type: {edge_type}')
        edge_key = (edge_type, source, target, path, line)
        if edge_key in seen:
            violations.append(f'duplicate edge: {edge_type} {source} -> {target}')
        seen.add(edge_key)
    return violations, seen


def _check_layer_imports(
    raw_edges: list[object],
    nodes: Mapping[str, Mapping[str, object]],
    config: object,
) -> list[str]:
    if not isinstance(config, Mapping):
        return []
    raw_rules = config.get('layers', ())
    rules = {
        str(item.get('name')): item
        for item in raw_rules
        if isinstance(item, Mapping) and item.get('name')
    }
    violations: list[str] = []
    for item in raw_edges:
        if not isinstance(item, Mapping) or item.get('type') != 'imports':
            continue
        source_node = nodes.get(str(item.get('source')))
        target_node = nodes.get(str(item.get('target')))
        if source_node is None or target_node is None:
            continue
        source_layer = source_node.get('layer')
        target_layer = target_node.get('layer')
        if not source_layer or not target_layer or source_layer == target_layer:
            continue
        rule = rules.get(str(source_layer))
        allows = set(rule.get('allows', ())) if rule else set()
        if str(target_layer) not in allows:
            violations.append(
                f'forbidden layer import: {source_layer} -> {target_layer} '
                f'({item.get("path")}:{item.get("line")})'
            )
    return violations


def check_graph(graph: Mapping[str, object]) -> list[str]:
    """Return structural and configured layer violations."""
    violations = (
        [f'unsupported schema_version: {graph.get("schema_version")!r}']
        if graph.get('schema_version') != SCHEMA_VERSION
        else []
    )
    raw_nodes = graph.get('nodes')
    raw_edges = graph.get('edges')
    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
        return [*violations, 'graph must contain nodes and edges arrays']
    nodes, node_violations = _index_nodes(raw_nodes)
    edge_violations, _ = _check_edges(raw_edges, nodes)
    violations.extend(node_violations)
    violations.extend(edge_violations)
    violations.extend(_check_layer_imports(raw_edges, nodes, graph.get('config')))
    return sorted(set(violations))


def explain_graph(graph: Mapping[str, object], query: str) -> str:
    """Render the nodes and relationships matching a module or symbol query."""
    nodes = [
        node
        for node in graph.get('nodes', ())
        if isinstance(node, Mapping)
        and query
        in {
            str(node.get('id')),
            str(node.get('name')),
            str(node.get('qualified_name')),
        }
    ]
    if not nodes:
        nodes = [
            node
            for node in graph.get('nodes', ())
            if isinstance(node, Mapping)
            and (
                str(node.get('name', '')).startswith(query)
                or str(node.get('qualified_name', '')).startswith(query)
            )
        ]
    if not nodes:
        return f'No graph node matches: {query}'

    node_ids = {str(node['id']) for node in nodes}
    lines: list[str] = []
    for node in sorted(nodes, key=lambda item: str(item['id'])):
        lines.append(f'{node["id"]} [{node["type"]}]')
        lines.append(f'  path: {node.get("path")}:{node.get("line")}')
        if node.get('layer'):
            lines.append(f'  layer: {node["layer"]}')
        outgoing = [
            edge
            for edge in graph.get('edges', ())
            if isinstance(edge, Mapping) and str(edge.get('source')) in node_ids
        ]
        incoming = [
            edge
            for edge in graph.get('edges', ())
            if isinstance(edge, Mapping) and str(edge.get('target')) in node_ids
        ]
        for label, edges in (('out', outgoing), ('in', incoming)):
            for edge in sorted(
                edges,
                key=lambda item: (
                    str(item.get('type')),
                    str(item.get('source')),
                    str(item.get('target')),
                ),
            ):
                other = edge['target'] if label == 'out' else edge['source']
                lines.append(f'  {label} {edge["type"]}: {other}')
    return '\n'.join(lines)


def _edge_identity(edge: Mapping[str, object]) -> tuple[str, str, str]:
    return str(edge.get('type')), str(edge.get('source')), str(edge.get('target'))


def diff_graphs(old: Mapping[str, object], new: Mapping[str, object]) -> dict[str, object]:
    """Return semantic node and edge differences between two graph snapshots."""
    old_nodes = {
        str(node['id']): node for node in old.get('nodes', ()) if isinstance(node, Mapping)
    }
    new_nodes = {
        str(node['id']): node for node in new.get('nodes', ()) if isinstance(node, Mapping)
    }
    old_edges = {
        _edge_identity(edge): edge for edge in old.get('edges', ()) if isinstance(edge, Mapping)
    }
    new_edges = {
        _edge_identity(edge): edge for edge in new.get('edges', ()) if isinstance(edge, Mapping)
    }
    changed_nodes = [
        {'id': node_id, 'old': old_nodes[node_id], 'new': new_nodes[node_id]}
        for node_id in sorted(set(old_nodes) & set(new_nodes))
        if old_nodes[node_id] != new_nodes[node_id]
    ]
    return {
        'source': {
            'old_revision': old.get('source', {}).get('revision')
            if isinstance(old.get('source'), Mapping)
            else None,
            'new_revision': new.get('source', {}).get('revision')
            if isinstance(new.get('source'), Mapping)
            else None,
        },
        'nodes': {
            'added': [new_nodes[node_id] for node_id in sorted(set(new_nodes) - set(old_nodes))],
            'removed': [old_nodes[node_id] for node_id in sorted(set(old_nodes) - set(new_nodes))],
            'changed': changed_nodes,
        },
        'edges': {
            'added': [new_edges[key] for key in sorted(set(new_edges) - set(old_edges))],
            'removed': [old_edges[key] for key in sorted(set(old_edges) - set(new_edges))],
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)

    build = commands.add_parser('build', help='build a graph JSON snapshot')
    build.add_argument('--root', type=Path, default=Path('.'))
    build.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    build.add_argument('--require-clean', action='store_true')

    check = commands.add_parser('check', help='check a graph snapshot')
    check.add_argument('--graph', type=Path, default=DEFAULT_OUTPUT)

    explain = commands.add_parser('explain', help='explain a module or symbol')
    explain.add_argument('query')
    explain.add_argument('--graph', type=Path, default=DEFAULT_OUTPUT)

    diff = commands.add_parser('diff', help='compare two graph snapshots')
    diff.add_argument('old', type=Path)
    diff.add_argument('new', type=Path)
    return parser


def _run_build(args: argparse.Namespace) -> int:
    graph = build_graph(args.root, require_clean=args.require_clean)
    write_graph(graph, args.output)
    print(f'[PASS] wrote {args.output} ({len(graph["nodes"])} nodes, {len(graph["edges"])} edges)')
    return 0


def _run_check(args: argparse.Namespace) -> int:
    violations = check_graph(read_graph(args.graph))
    if violations:
        print('[FAIL] Code Graph violations:')
        print('\n'.join(f' - {item}' for item in violations))
        return 1
    print(f'[PASS] {args.graph} is valid')
    return 0


def _run_explain(args: argparse.Namespace) -> int:
    print(explain_graph(read_graph(args.graph), args.query))
    return 0


def _run_diff(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            diff_graphs(read_graph(args.old), read_graph(args.new)),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


_COMMANDS: dict[str, Callable[[argparse.Namespace], int]] = {
    'build': _run_build,
    'check': _run_check,
    'explain': _run_explain,
    'diff': _run_diff,
}


def main(argv: list[str] | None = None) -> int:
    """Run the Code Graph CLI."""
    args = _parser().parse_args(argv)
    try:
        result = _COMMANDS[args.command](args)
    except (OSError, TypeError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f'[FAIL] {exc}', file=sys.stderr)
        result = 2
    return result


if __name__ == '__main__':
    raise SystemExit(main())
