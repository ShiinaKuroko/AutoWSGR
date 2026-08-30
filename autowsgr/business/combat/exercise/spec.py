"""演习任务定义的入口转换。

这里只把已通过文件读取的参数转换为演习可执行的领域对象；页面操作和
任务生命周期仍由执行器与处理器负责。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from autowsgr.infra.combat import CombatMode, CombatPlan
from autowsgr.infra.fleet import (
    ResolvedFleetSelection,
    resolve_fleet_selection,
)


EXERCISE_FIELDS = frozenset(
    {
        'name',
        'mode',
        'schema_version',
        'fleet_id',
        'fleet',
        'fleet_rules',
        'fleet_presets',
        'rival',
        'rivals_limit',
        'repair_mode',
        'fight_condition',
        'node_defaults',
        'node_args',
        'selected_nodes',
    },
)


@dataclass(frozen=True, slots=True)
class ExerciseSpec:
    """一张已校验的演习任务定义。"""

    plan: CombatPlan
    fleet_selection: ResolvedFleetSelection
    rival: int | None = None
    rivals_limit: int | None = None

    @classmethod
    def from_params(cls, params: Mapping[str, Any]) -> ExerciseSpec:
        """把 YAML 参数转换为演习计划和唯一舰队选择。"""
        unknown = sorted(set(params) - EXERCISE_FIELDS)
        if unknown:
            raise ValueError(f'演习 YAML 包含未知字段: {", ".join(unknown)}')

        data = dict(params)
        _validate_positive_optional(data, 'rival', maximum=5)
        _validate_positive_optional(data, 'rivals_limit', maximum=5)
        _normalize_fleet_sources(data)

        fleet_id = data.get('fleet_id', 1)
        _validate_fleet_id(fleet_id)
        _normalize_plan_data(data)

        try:
            plan = CombatPlan.from_dict(data, name=str(data.get('name') or '演习'))
            selection = resolve_fleet_selection(plan, fleet_id=fleet_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f'演习 YAML 字段校验失败: {exc}') from exc

        return cls(
            plan=plan,
            fleet_selection=selection,
            rival=data.get('rival'),
            rivals_limit=data.get('rivals_limit'),
        )


def _normalize_fleet_sources(data: dict[str, Any]) -> None:
    """校验互斥的舰队来源并统一规则列表形态。"""
    if data.get('fleet') is not None and (
        data.get('fleet_rules') is not None or data.get('fleet_presets') is not None
    ):
        raise ValueError('演习不能同时提供 fleet 与 fleet_rules/fleet_presets')

    raw_rules = data.pop('fleet_rules', None)
    if raw_rules is not None:
        if data.get('fleet_presets') is not None:
            raise ValueError('演习不能同时提供 fleet_rules 和 fleet_presets')
        data['fleet_presets'] = [{'ships': raw_rules}]

    fleet = data.get('fleet')
    if fleet is not None:
        if not isinstance(fleet, list) or not 1 <= len(fleet) <= 6:
            raise ValueError('演习字段 fleet 必须是 1-6 艘舰船名称列表')
        if any(not isinstance(name, str) or not name.strip() for name in fleet):
            raise ValueError('演习字段 fleet 必须是非空字符串列表')

    presets = data.get('fleet_presets')
    if presets is None:
        return
    if not isinstance(presets, list):
        raise ValueError('演习字段 fleet_presets 必须是列表')  # noqa: TRY004
    for preset in presets:
        if not isinstance(preset, Mapping):
            raise ValueError('演习字段 fleet_presets 每项必须是对象')  # noqa: TRY004
        ships = preset.get('ships')
        if not isinstance(ships, list) or not 1 <= len(ships) <= 6:
            raise ValueError('演习舰队 ships 必须包含 1-6 个槽位')


def _validate_fleet_id(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 4:
        raise ValueError('演习字段 fleet_id 必须在 1-4 范围内')


def _normalize_plan_data(data: dict[str, Any]) -> None:
    raw_mode = data.get('mode')
    if raw_mode is not None and raw_mode != CombatMode.EXERCISE:
        raise ValueError('演习 YAML 的 mode 必须为 exercise')
    data['mode'] = CombatMode.EXERCISE

    defaults = dict(data.get('node_defaults') or {})
    defaults.setdefault('formation', 1)
    defaults.setdefault('night', True)
    data['node_defaults'] = defaults


def _validate_positive_optional(params: Mapping[str, Any], name: str, *, maximum: int) -> None:
    value = params.get(name)
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise ValueError(f'演习字段 {name} 必须在 1-{maximum} 范围内')
