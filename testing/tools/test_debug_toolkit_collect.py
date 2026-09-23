"""Debug toolkit OCR sample collection tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
import pytest

from autowsgr.common.device import adb

from tools.debug_toolkit.function import collect


def _team_screen(*, occupied_slots: tuple[int, ...] = ()) -> np.ndarray:
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    no_ship_bgr = np.array((112, 87, 43), dtype=np.uint8)
    normal_bgr = np.array((118, 168, 75), dtype=np.uint8)
    for slot, (x_ratio, y_ratio) in collect.TEAM_BLOOD_PROBES.items():
        x = round(x_ratio * screen.shape[1])
        y = round(y_ratio * screen.shape[0])
        screen[y, x] = normal_bgr if slot in occupied_slots else no_ship_bgr
    return screen


def test_crop_team_filters_empty_slots_and_saves_four_scales(tmp_path: Path):
    screen = _team_screen(occupied_slots=(1,))

    valid_slots, saved_images = collect.crop_team(screen, tmp_path)

    assert valid_slots == 1
    assert saved_images == 12
    assert (tmp_path / 'team/name/Team-slot-1-name-1X.png').is_file()
    assert (tmp_path / 'team/level/Team-slot-1-level-4X.png').is_file()
    assert (tmp_path / 'team/type/Team-slot-1-type-3X.png').is_file()
    assert not (tmp_path / 'team/name/Team-slot-2-name-1X.png').exists()


def test_team_scaled_crop_uses_requested_size(tmp_path: Path):
    screen = _team_screen(occupied_slots=(1,))
    collect.crop_team(screen, tmp_path)

    original = cv2.imread(str(tmp_path / 'team/name/Team-slot-1-name-1X.png'))
    enlarged = cv2.imread(str(tmp_path / 'team/name/Team-slot-1-name-4X.png'))

    assert original is not None
    assert enlarged is not None
    expected_shape = (original.shape[0] * 4, original.shape[1] * 4)
    assert abs(enlarged.shape[0] - expected_shape[0]) <= 1
    assert abs(enlarged.shape[1] - expected_shape[1]) <= 1


def test_crop_pool_uses_dll_row_and_filters_empty_cards(tmp_path: Path):
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    screen[350:360, 110:135] = 255

    valid_cards, saved_images = collect.crop_pool(
        screen,
        tmp_path,
        locator=lambda _image: [(346, 372)],
    )

    assert valid_cards == 1
    assert saved_images == 12
    assert (tmp_path / 'pool/name/Pool-slot-1-name-1X.png').is_file()
    assert (tmp_path / 'pool/level/Pool-slot-1-level-2X.png').is_file()
    assert (tmp_path / 'pool/type/Pool-slot-1-type-4X.png').is_file()
    assert not (tmp_path / 'pool/name/Pool-slot-2-name-1X.png').exists()


def test_crop_pool_preserves_physical_slot_number(tmp_path: Path):
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    screen[350:360, 250:275] = 255

    valid_cards, _saved_images = collect.crop_pool(
        screen,
        tmp_path,
        locator=lambda _image: [(346, 372)],
    )

    assert valid_cards == 1
    assert (tmp_path / 'pool/name/Pool-slot-2-name-1X.png').is_file()
    assert not (tmp_path / 'pool/name/Pool-slot-1-name-1X.png').exists()


def test_crop_pool_rejects_page_without_dll_rows(tmp_path: Path):
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)

    with pytest.raises(collect.CropToolError, match='DLL 未定位到船池名称条'):
        collect.crop_pool(screen, tmp_path, locator=lambda _image: [])


def test_prepare_summary_target_appends_sequence_and_builds_tree(tmp_path: Path):
    now = datetime(2026, 8, 8, 12, 34, 56, tzinfo=UTC)

    first = collect.prepare_capture_target(tmp_path, 'summary', 'team', now)
    (first.root / f'adb-team{first.suffix}.png').touch()
    second = collect.prepare_capture_target(tmp_path, 'summary', 'team', now)

    assert first.root == tmp_path / '20260808'
    assert first.suffix == '-001'
    assert second.suffix == '-002'
    assert (first.root / 'team/name').is_dir()
    assert (first.root / 'pool/level').is_dir()
    assert (first.root / 'pool/type').is_dir()


def test_prepare_timestamp_target_uses_second_precision(tmp_path: Path):
    now = datetime(2026, 8, 8, 12, 34, 56, tzinfo=UTC)

    first = collect.prepare_capture_target(tmp_path, 'timestamp', 'pool', now)
    (first.root / f'adb-pool{first.suffix}.png').touch()
    second = collect.prepare_capture_target(tmp_path, 'timestamp', 'pool', now)

    assert first.root == tmp_path / '20260808-123456'
    assert first.suffix == ''
    assert second.suffix == '-002'


def test_prepare_target_uses_first_free_sequence_after_a_gap(tmp_path: Path):
    now = datetime(2026, 8, 8, 12, 34, 56, tzinfo=UTC)
    root = tmp_path / '20260808'
    root.mkdir()
    (root / 'adb-team.png').touch()
    (root / 'adb-team-003.png').touch()

    target = collect.prepare_capture_target(tmp_path, 'summary', 'team', now)

    assert target.suffix == '-002'


def test_adb_command_accepts_custom_serial(monkeypatch: pytest.MonkeyPatch):
    calls: list[tuple[Path, str]] = []
    monkeypatch.setattr(adb, 'find_adb', lambda _explicit: Path('adb.exe'))
    monkeypatch.setattr(
        adb,
        'connect',
        lambda serial, adb_path: calls.append((adb_path, serial)),
    )

    result = collect.main(['adb', '127.0.0.1:5555'])

    assert result == 0
    assert calls == [(Path('adb.exe'), '127.0.0.1:5555')]


def test_save_serial_does_not_block_capture_when_config_is_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReadOnlyPath:
        def write_text(self, *_args: object, **_kwargs: object) -> None:
            raise OSError('read-only')

    def config_path() -> ReadOnlyPath:
        return ReadOnlyPath()

    monkeypatch.setattr(collect, '_config_path', config_path)

    collect._save_serial('127.0.0.1:16384')


def test_raw_only_capture_skips_roi_cropping(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    monkeypatch.setattr(adb, 'find_adb', lambda _explicit: Path('adb.exe'))
    monkeypatch.setattr(adb, 'capture_screen', lambda *_args: screen)
    monkeypatch.setattr(collect, '_read_saved_serial', lambda: '127.0.0.1:16384')

    result = collect.main(['team', '--raw-only', '--output', str(tmp_path)])

    assert result == 0
    assert list(tmp_path.glob('*/adb-team*.png'))
    assert not list(tmp_path.rglob('team/name/*.png'))
