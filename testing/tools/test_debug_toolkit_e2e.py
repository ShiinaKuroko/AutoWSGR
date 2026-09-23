"""Tests for unified debug toolkit E2E argument handling."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from tools.debug_toolkit.function.e2e_runner import run as e2e_run
from tools.debug_toolkit.function.e2e_runner.cases import campaign, decisive_stability, exercise
from tools.debug_toolkit.function.e2e_runner.cases.change_fleet import _parse_ships


def test_parse_ships_pads_to_six_slots() -> None:
    assert _parse_ships('U-47,U-96') == ['U-47', 'U-96', None, None, None, None]


def test_default_campaign_and_exercise_fixtures_are_packaged_from_repo_root() -> None:
    assert Path(campaign._DEFAULT_YAML).is_file()
    assert Path(exercise._DEFAULT_YAML).is_file()


def test_parse_ships_rejects_more_than_six_slots() -> None:
    with pytest.raises(argparse.ArgumentTypeError, match='最多支持 6'):
        _parse_ships('a,b,c,d,e,f,g')


def test_decisive_stability_case_is_discoverable_and_keeps_cli_contract() -> None:
    parser = argparse.ArgumentParser()
    decisive_stability.add_arguments(parser)

    args = parser.parse_args(
        [
            '--tickets',
            '2',
            '--leaves-per-ticket',
            '1',
            '--retreat-node',
            'B',
            '--stop-after-tickets',
        ]
    )

    assert args.tickets == 2
    assert args.leaves_per_ticket == 1
    assert args.retreat_node == 'B'
    assert args.stop_after_tickets is True
    assert 'decisive_stability' in e2e_run.load_cases()
