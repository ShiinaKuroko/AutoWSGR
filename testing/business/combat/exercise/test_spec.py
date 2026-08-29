"""演习任务定义的静态准入回归。"""

from __future__ import annotations

from pathlib import Path

import pytest

from autowsgr.business.combat.exercise.spec import ExerciseSpec
from autowsgr.combat import CombatMode


def _params() -> dict:
    return {
        'fleet_id': 2,
        'fleet_presets': [
            {
                'name': '队伍2',
                'ships': [
                    {'name': 'U-177', 'ship_type': ['ss'], 'min_level': 69},
                    {'name': '阿尔戈'},
                    {'name': '卡萨比安卡'},
                    {'name': 'U-103'},
                    {'name': 'S-198', 'candidates': ['S189']},
                    {'candidates': ['阿尔汉格尔斯克', '水貂']},
                ],
            },
        ],
    }


def test_exercise_spec_converts_team_rules() -> None:
    spec = ExerciseSpec.from_params(_params())

    assert spec.plan.mode == CombatMode.EXERCISE
    assert spec.plan.default_node.night is True
    assert spec.fleet_selection.fleet_id == 2
    rules = spec.fleet_selection.slot_rules
    assert rules is not None
    assert len(rules) == 6
    assert rules[0].primary is not None
    assert rules[0].primary.ship_types
    assert rules[0].primary.min_level == 69
    assert [option.name for option in rules[4].options] == ['S-198', 'S189']
    assert rules[5].primary is None
    assert [option.name for option in rules[5].options] == ['阿尔汉格尔斯克', '水貂']


def test_exercise_spec_rejects_bad_mode_and_unknown_field() -> None:
    with pytest.raises(ValueError, match='mode'):
        ExerciseSpec.from_params({**_params(), 'mode': 'normal'})
    with pytest.raises(ValueError, match='未知字段'):
        ExerciseSpec.from_params({**_params(), 'unexpected': True})


def test_exercise_spec_accepts_api_style_fleet_rules() -> None:
    params = {
        'fleet_id': 2,
        'fleet_rules': [
            {'name': 'U-177', 'ship_type': ['ss'], 'min_level': 69},
        ],
    }
    spec = ExerciseSpec.from_params(params)
    assert spec.fleet_selection.slot_rules is not None
    assert spec.fleet_selection.slot_rules[0].primary.name == 'U-177'


def test_exercise_spec_accepts_chinese_type_and_strict_aliases() -> None:
    spec = ExerciseSpec.from_params(
        {
            'fleet_id': 2,
            'fleet_presets': [
                {
                    'ships': [
                        {
                            'name': 'U-177',
                            'type': '潜艇',
                            'min_level': 69,
                            'strict': True,
                        },
                        {'alternatives': ['阿尔汉格尔斯克', '水貂']},
                    ],
                },
            ],
        },
    )
    first, second = spec.fleet_selection.slot_rules
    assert first.primary.ship_types[0].value == '潜艇'
    assert first.primary.relaxed_constraints is False
    assert [item.name for item in second.options] == ['阿尔汉格尔斯克', '水貂']


def test_exercise_spec_rejects_conflicting_or_oversized_fleet_sources() -> None:
    with pytest.raises(ValueError, match='不能同时提供'):
        ExerciseSpec.from_params({**_params(), 'fleet': ['U-177']})
    with pytest.raises(ValueError, match='1-6'):
        ExerciseSpec.from_params({'fleet_id': 2, 'fleet': ['A'] * 7})


def test_exercise_fixture_is_yaml_compatible() -> None:
    path = Path(__file__).parents[3] / 'fixtures' / 'exercise_team2.yaml'
    assert path.is_file()
