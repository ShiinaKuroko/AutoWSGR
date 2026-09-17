"""验证 common/device 的当前重写契约。"""

from __future__ import annotations

import subprocess
from pathlib import Path

import cv2
import numpy
import pytest

from autowsgr.common import device
from autowsgr.common.device.adb_engine import executor
from autowsgr.common.device.config import DeviceConfig
from autowsgr.common.device.device_engine.foundation import delay, platform
from autowsgr.common.device.device_engine.orchestration import discovery, lifecycle, screenshot
from autowsgr.common.device.errors import DeviceConnectionError
from autowsgr.common.device.scrcpy_engine.executor import ScrcpyEngine


def test_device_exports_only_service_namespace() -> None:
    """根包只暴露统一 service 模块。"""
    assert device.__all__ == ['service']
    assert device.service.DeviceService
    assert not hasattr(device, 'DeviceService')


def test_service_starts_with_a_disconnected_session() -> None:
    """统一服务创建后拥有默认分辨率且尚未连接。"""
    service = device.service.DeviceService()

    assert service.resolution == (0, 0)
    assert not service.is_connected()


def test_device_config_accepts_owned_fields_and_rejects_unknown_fields() -> None:
    """配置模型只接受当前 device 所有的字段。"""
    config = DeviceConfig(
        ADB_CONNECTION='127.0.0.1:16384',
        DEVICE_OPERATION_DELAY_MIN=0.1,
        DEVICE_OPERATION_DELAY_MAX=0.2,
    )

    assert config.ADB_CONNECTION == '127.0.0.1:16384'
    assert config.DEVICE_OPERATION_DELAY_MIN == 0.1
    with pytest.raises(ValueError, match='Extra inputs are not permitted'):
        DeviceConfig(DEVICE_OLD_OPTION=True)


def test_adb_resources_and_explicit_path_resolution() -> None:
    """ADB 执行器包含随包资源并支持显式路径。"""
    bundled_adb = Path(executor.__file__).with_name('adb.exe')

    assert bundled_adb.is_file()
    assert (bundled_adb.parent / 'AdbWinApi.dll').is_file()
    assert (bundled_adb.parent / 'AdbWinUsbApi.dll').is_file()
    assert executor.find_adb_executable(bundled_adb) == bundled_adb.resolve()


def test_read_adb_devices_parses_status_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    """设备列表读取会跳过标题并保留 serial 和状态。"""
    result = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='List of devices attached\nserial-a\tdevice\nserial-b\tunauthorized\n',
        stderr='',
    )
    monkeypatch.setattr(executor, 'find_adb_executable', lambda _path=None: Path('adb.exe'))
    monkeypatch.setattr(executor, '_execute_adb_command', lambda *_args, **_kwargs: result)

    assert executor.read_adb_devices() == [
        ('serial-a', 'device'),
        ('serial-b', 'unauthorized'),
    ]


def test_connect_adb_device_confirms_device_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADB 连接必须在 get-state 返回 device 后才算成功。"""
    responses = iter(
        [
            subprocess.CompletedProcess([], 0, stdout='connected', stderr=''),
            subprocess.CompletedProcess([], 0, stdout='device\n', stderr=''),
        ]
    )
    monkeypatch.setattr(executor, 'find_adb_executable', lambda _path=None: Path('adb.exe'))
    monkeypatch.setattr(
        executor,
        '_execute_adb_command',
        lambda *_args, **_kwargs: next(responses),
    )

    executor.connect_adb_device('serial-a')


def test_capture_device_screenshot_returns_bgr_image(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADB 截图会把 PNG 字节解码为 BGR 数组。"""
    source = numpy.zeros((2, 3, 3), dtype=numpy.uint8)
    source[:, :] = (0, 0, 255)
    success, encoded = cv2.imencode('.png', source)
    assert success
    responses = iter(
        [
            subprocess.CompletedProcess([], 0, stdout='connected', stderr=''),
            subprocess.CompletedProcess([], 0, stdout='device\n', stderr=''),
            subprocess.CompletedProcess([], 0, stdout=encoded.tobytes(), stderr=b''),
        ]
    )
    monkeypatch.setattr(executor, 'find_adb_executable', lambda _path=None: Path('adb.exe'))
    monkeypatch.setattr(
        executor,
        '_execute_adb_command',
        lambda *_args, **_kwargs: next(responses),
    )

    screen = executor.capture_device_screenshot('serial-a')

    assert screen.shape == (2, 3, 3)
    assert tuple(screen[0, 0]) == (0, 0, 255)


def test_screenshot_workflow_delegates_to_system_files(monkeypatch: pytest.MonkeyPatch) -> None:
    """截图保存流程将 RGB 帧和允许目录交给 system.files。"""
    frame = numpy.zeros((2, 2, 3), dtype=numpy.uint8)
    saved: dict[str, object] = {}

    class FakeScrcpy:
        def capture_screenshot(self) -> numpy.ndarray:
            return frame

    class FakeSession:
        scrcpy = FakeScrcpy()

    def record_save(
        image: numpy.ndarray,
        path: str,
        *,
        allowed_root: str,
    ) -> None:
        saved['image'] = image
        saved['path'] = path
        saved['allowed_root'] = allowed_root

    monkeypatch.setattr(screenshot.files, 'save_image', record_save)

    screenshot._save_device_screenshot(
        FakeSession(),
        'capture.png',
        allowed_root='captures',
    )

    assert saved['image'] is frame
    assert saved['path'] == 'capture.png'
    assert saved['allowed_root'] == 'captures'


def test_discovery_resolves_explicit_connection_and_recognizes_emulator() -> None:
    """设备发现优先使用显式连接地址，并识别已知 serial。"""
    config = DeviceConfig(
        ADB_CONNECTION='127.0.0.1:16384',
        DEVICE_EMULATOR_TYPE='MuMu',
    )

    assert discovery.recognize_emulator_type('127.0.0.1:16384') is platform.EmulatorType.mumu
    assert discovery.recognize_emulator_type('unknown') is None
    assert discovery.resolve_device_serial(config) == '127.0.0.1:16384'


def test_discovery_filters_offline_devices(monkeypatch: pytest.MonkeyPatch) -> None:
    """候选发现只返回 ADB 状态为 device 的设备。"""
    monkeypatch.setattr(
        executor,
        'read_adb_devices',
        lambda _path=None: [
            ('unknown', 'device'),
            ('127.0.0.1:16384', 'device'),
            ('offline-device', 'offline'),
        ],
    )

    candidates = discovery.discover_emulator_candidates()

    assert [candidate.serial for candidate in candidates] == [
        '127.0.0.1:16384',
        'unknown',
    ]


def test_discovery_rejects_empty_candidate_selection() -> None:
    """没有候选设备时不能进入交互选择。"""
    with pytest.raises(DeviceConnectionError, match='没有可供选择'):
        discovery.select_emulator_candidate([])


def test_platform_and_lifecycle_use_explicit_semantics() -> None:
    """平台计算和生命周期工厂返回当前宿主管理器契约。"""
    config = DeviceConfig(DEVICE_EMULATOR_TYPE='云手机')
    manager = lifecycle.create_emulator_process_manager(config, platform.OSType.windows)

    assert (
        platform.calculate_default_emulator_serial(
            platform.EmulatorType.mumu,
            platform.OSType.windows,
        )
        == '127.0.0.1:16384'
    )
    assert manager.check_emulator_running()
    manager.start_emulator()
    manager.stop_emulator()


def test_timing_calculates_configured_operation_delay() -> None:
    """操作延迟计算使用配置的上下界。"""
    delay.configure_operation_delay_bounds(0.2, 0.2)
    try:
        assert delay.calculate_operation_delay() == 0.2
    finally:
        delay.configure_operation_delay_bounds(0.0, 0.0)


def test_timing_rejects_inverted_bounds() -> None:
    """操作延迟下界大于上界时直接拒绝。"""
    with pytest.raises(ValueError, match='0 <= minimum <= maximum'):
        delay.configure_operation_delay_bounds(0.2, 0.1)


def test_scrcpy_engine_exposes_named_channel_and_input_methods() -> None:
    """Scrcpy 执行器出口使用通道、截图和输入的业务名称。"""
    engine = ScrcpyEngine()

    assert engine.resolution == (0, 0)
    assert not engine.is_scrcpy_connected()
    assert engine.connect_scrcpy
    assert engine.capture_screenshot
    assert engine.click_screen
    assert engine.swipe_screen
    assert engine.long_press_screen
    assert engine.send_key_event
    assert engine.input_text
