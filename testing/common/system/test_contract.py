"""验证 common/system 的公开出口和运行契约。"""

import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from autowsgr.common import system
from autowsgr.common.device.errors import GameError, NetworkError, ResourceError
from autowsgr.common.system.config import LogConfig
from autowsgr.common.system.enums import BaseEnum, IntEnum, StrEnum
from autowsgr.common.system.errors import (
    ApplicationError,
    BusinessError,
    CommonError,
    DispatchError,
    SystemError,
)
from autowsgr.common.TEMP.exceptions import (
    CombatDecisionError,
    CombatRecognitionTimeoutError,
    CriticalError,
    DockFullError,
    ImageNotFoundError,
    ManualRepairRequiredError,
    NavigationError,
    OCRError,
    PageNotFoundError,
)


def test_system_exposes_only_capability_namespaces() -> None:
    assert system.__all__ == ['enums', 'errors', 'files', 'logger']
    assert not hasattr(system, 'load_yaml')
    assert not hasattr(system, 'merge_dicts')
    assert not hasattr(system, 'save_image')


def test_system_enums_provide_only_common_base_behavior() -> None:
    class Mode(IntEnum):
        READY = 1

    class Label(StrEnum):
        READY = 'ready'

    assert Mode.READY == 1
    assert Label.READY == 'ready'
    assert issubclass(Mode, BaseEnum)
    with pytest.raises(ValueError, match='不是合法的 Mode'):
        Mode(2)


def test_system_errors_expose_only_program_layer_bases() -> None:
    assert system.errors.__all__ == [
        'ApplicationError',
        'BusinessError',
        'CommonError',
        'DispatchError',
        'SystemError',
    ]
    assert all(
        issubclass(error, SystemError)
        for error in (CommonError, ApplicationError, BusinessError, DispatchError)
    )
    assert not hasattr(system.errors, 'AutoWSGRError')


def test_temporary_concrete_errors_use_program_layer_bases() -> None:
    assert all(issubclass(error, CommonError) for error in (OCRError, ImageNotFoundError))
    assert all(
        issubclass(error, ApplicationError) for error in (PageNotFoundError, NavigationError)
    )
    assert all(
        issubclass(error, BusinessError)
        for error in (
            ManualRepairRequiredError,
            DockFullError,
            CombatRecognitionTimeoutError,
            CombatDecisionError,
        )
    )
    assert issubclass(CriticalError, SystemError)


def test_device_owns_game_error_categories() -> None:
    assert issubclass(GameError, CommonError)
    assert issubclass(NetworkError, GameError)
    assert issubclass(ResourceError, GameError)


def test_log_config_accepts_owner_prefixed_fields(tmp_path: Path) -> None:
    config = LogConfig.model_validate(
        {
            'LOG_LEVEL': 'INFO',
            'LOG_SYSTEM_DIR': tmp_path,
            'LOG_COMBAT_OPEN': True,
        },
    )

    assert config.LOG_LEVEL == 'INFO'
    assert config.LOG_USER_DIR is not None
    assert config.LOG_COMBAT_OPEN
    with pytest.raises(ValueError, match='LOG_LEVEL'):
        LogConfig(LOG_LEVEL='CRITICAL')
    with pytest.raises(ValueError, match='channels'):
        LogConfig.model_validate({'channels': {'combat': 'DEBUG'}})


def test_logger_patcher_uses_beijing_time() -> None:
    record = {
        'time': datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        'file': SimpleNamespace(path=__file__, name=Path(__file__).name),
        'line': 1,
        'extra': {},
    }

    system.logger._src_patcher(record)

    assert record['time'].isoformat() == '2026-01-01T08:00:00+08:00'


def test_logger_setup_uses_config(tmp_path: Path) -> None:
    log_dir = tmp_path / 'logs'
    system.logger.setup_logger(LogConfig(LOG_USER_DIR=log_dir))

    assert log_dir.is_dir()
    assert system.logger.get_logger('common.system.test') is not None


def test_logger_debug_output_uses_module_open_switch(tmp_path: Path) -> None:
    log_dir = tmp_path / 'logs'
    system.logger.setup_logger(
        LogConfig(LOG_LEVEL='INFO', LOG_USER_DIR=log_dir, LOG_COMBAT_OPEN=True),
    )

    system.logger.get_logger('combat').debug('combat debug marker')
    system.logger.get_logger('combat.recognition').debug('combat child debug marker')
    system.logger.get_logger('ui').debug('ui debug marker')

    log_file = next(log_dir.glob('autowsgr_*.log'))
    output = log_file.read_text(encoding='utf-8')
    assert 'combat debug marker' in output
    assert 'combat child debug marker' in output
    assert 'ui debug marker' not in output


def test_files_yaml_round_trip_and_root_check(tmp_path: Path) -> None:
    target = tmp_path / 'nested' / 'state.yaml'
    system.files.save_yaml(
        {'舰船': ['胡德'], 'enabled': True},
        target,
        allowed_root=tmp_path,
    )

    assert system.files.load_yaml(target, allowed_root=tmp_path) == {
        '舰船': ['胡德'],
        'enabled': True,
    }

    outside = tmp_path.parent / f'{tmp_path.name}-outside.yaml'
    with pytest.raises(ValueError, match='超出允许目录'):
        system.files.load_yaml(outside, allowed_root=tmp_path)


def test_files_save_preserves_original_when_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / 'state.yaml'
    system.files.save_yaml({'version': 1}, target, allowed_root=tmp_path)

    def fail_replace(*_: object) -> None:
        raise OSError('replace failed')

    monkeypatch.setattr(system.files.os, 'replace', fail_replace)
    with pytest.raises(OSError, match='replace failed'):
        system.files.save_yaml({'version': 2}, target, allowed_root=tmp_path)

    assert system.files.load_yaml(target, allowed_root=tmp_path) == {'version': 1}
    assert not list(tmp_path.glob(f'.{target.name}.*.tmp'))
