"""Tests for unified debug toolkit E2E argument handling."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from autowsgr.dispatch.context import ContextNotBoundError, context

from tools.debug_toolkit.function.e2e_runner import run as e2e_run
from tools.debug_toolkit.function.e2e_runner.cases import campaign, decisive_stability, exercise
from tools.debug_toolkit.function.e2e_runner.cases.change_fleet import _parse_ships
from tools.debug_toolkit.function.e2e_runner.framework import E2ERunner
from tools.debug_toolkit.function.screenshot import save_image


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


class _FakeDevice:
    """E2E 只读准备阶段使用的设备服务替身。"""

    def __init__(self, config: object = None) -> None:
        self.config = config
        self.disconnected = False

    def connect(self) -> SimpleNamespace:
        return SimpleNamespace(serial='fake-0001', resolution=(960, 540))

    def screenshot(self) -> np.ndarray:
        return np.zeros((4, 4, 3), dtype=np.uint8)

    def disconnect(self) -> None:
        self.disconnected = True


def test_save_image_writes_png_file(tmp_path: Path) -> None:
    """失败截图工具链不依赖旧 device.adb 模块即可落盘 PNG。"""
    image = np.zeros((4, 6, 3), dtype=np.uint8)

    path = save_image(image, tag='unit', img_dir=tmp_path)

    assert path is not None
    assert path.suffix == '.png'
    assert path.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'


def test_readonly_prepare_binds_context_and_cleanup_releases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--no-launch 连接设备后把已绑定 runtime 的 ContextHandle 交给 case。"""
    monkeypatch.setattr('autowsgr.common.device.service.DeviceService', _FakeDevice)

    runner = E2ERunner('screenshot', SimpleNamespace(), no_launch=True)

    assert runner.prepare() is True
    assert runner.ctx.runtime.ctrl.disconnected is False
    assert runner.ctx.runtime.config is None

    runner.cleanup()

    with pytest.raises(ContextNotBoundError):
        context.request()


def test_prepare_without_no_launch_reports_missing_navigator() -> None:
    """完整实机链路未接通时给出指向 navigation.goto_page 的失败记录。"""
    runner = E2ERunner('screenshot', SimpleNamespace(), no_launch=False)

    assert runner.prepare() is False
    assert any('goto_page' in (step.error or '') for step in runner.state.steps)
