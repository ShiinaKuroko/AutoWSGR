"""模块功能：执行主机侧 ADB 能力。

上层调用：
- common.device.device_engine.orchestration.connection 和 discovery：定位 ADB 并读写设备列表。
- common.device.device_engine.orchestration.lifecycle：重启 ADB 服务和截取设备画面。

下层依赖：
- Python 标准库和 OpenCV：提供进程执行与图像解码。
- common.device.errors：提供设备错误类型。
- 随包 ADB 资源：提供主机侧可执行文件。

边界：只定位并执行 ADB，不选择业务设备、不管理模拟器进程、不编排页面流程。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import cv2
import numpy

from autowsgr.common.device.errors import DeviceConnectionError, DeviceNotFoundError
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Sequence


_log = get_logger('device.adb')


# ── ADB 资源和命令参数 ──────────────────────────────────────────────────────

_ADB_ENGINE_DIR = Path(__file__).resolve().parent
_BUNDLED_ADB_PATH = _ADB_ENGINE_DIR / 'adb.exe'
_ADB_COMMAND_TIMEOUT_SECONDS = 10.0
_ADB_CONNECT_TIMEOUT_SECONDS = 5.0
_ADB_SERVER_RESTART_DELAY_SECONDS = 1.0
_ADB_SERVER_START_TIMEOUT_SECONDS = 8.0


def find_adb_executable(adb_path: str | Path | None = None) -> Path:
    """定位可执行的 ADB。

    Args:
        adb_path: 显式 ADB 路径；未提供时按系统 PATH、随包资源和宿主安装目录查找。

    Returns:
        可执行的 ADB 文件路径。

    Raises:
        DeviceNotFoundError: 显式路径或自动查找均未找到可用 ADB。
    """
    if adb_path is not None:
        explicit = Path(adb_path).expanduser().resolve()
        if explicit.is_file():
            return explicit
        raise DeviceNotFoundError(f'找不到指定的 ADB: {explicit}')

    if system_adb := shutil.which('adb'):
        path = Path(system_adb).resolve()
        _log.debug('[DEVICE] ADB → 定位：source={!r}, path={!r}', 'path', str(path))
        return path

    if sys.platform.startswith('win') and _BUNDLED_ADB_PATH.is_file():
        _log.debug(
            '[DEVICE] ADB → 定位：source={!r}, path={!r}',
            'bundled',
            str(_BUNDLED_ADB_PATH),
        )
        return _BUNDLED_ADB_PATH

    if sys.platform.startswith('win'):
        for candidate in _find_windows_registry_adb_paths():
            path = Path(candidate)
            if path.is_file():
                _log.debug(
                    '[DEVICE] ADB → 定位：source={!r}, path={!r}',
                    'registry',
                    str(path),
                )
                return path

    raise DeviceNotFoundError('未找到 ADB 可执行文件，请检查设备资源或宿主 ADB 安装。')


def read_adb_devices(adb_path: str | Path | None = None) -> list[tuple[str, str]]:
    """读取当前 ADB 设备及其状态。

    Args:
        adb_path: 显式 ADB 路径；未提供时使用 device 的路径规则。

    Returns:
        设备的 ``(serial, status)`` 列表，不包含 ADB 标题行。

    Raises:
        DeviceConnectionError: ADB 命令失败或执行超时。
        DeviceNotFoundError: 没有找到 ADB 可执行文件。
    """
    executable = find_adb_executable(adb_path)
    result = _execute_adb_command(executable, ['devices'])
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise DeviceConnectionError(f'读取 ADB 设备列表失败: {detail}')

    devices: list[tuple[str, str]] = []
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith('list of devices'):
            continue
        parts = line.split()
        if len(parts) >= 2:
            devices.append((parts[0], parts[1]))
    return devices


def connect_adb_device(serial: str, adb_path: str | Path | None = None) -> None:
    """连接指定 serial，并确认设备状态为 ``device``。

    Args:
        serial: 目标设备的 ADB serial。
        adb_path: 显式 ADB 路径；未提供时使用 device 的路径规则。

    Raises:
        DeviceConnectionError: 连接失败或设备未进入可用状态。
        DeviceNotFoundError: 没有找到 ADB 可执行文件。
    """
    executable = find_adb_executable(adb_path)
    result = _execute_adb_command(executable, ['connect', serial], timeout=5.0)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise DeviceConnectionError(f'连接设备失败: {detail or serial}')

    state = _execute_adb_command(executable, ['-s', serial, 'get-state'], timeout=5.0)
    if state.returncode != 0 or state.stdout.strip() != 'device':
        detail = (state.stderr or state.stdout).strip()
        raise DeviceConnectionError(f'设备未就绪: {detail or serial}')


def capture_device_screenshot(
    serial: str,
    adb_path: str | Path | None = None,
) -> numpy.ndarray:
    """通过 ADB 截取当前画面并返回 OpenCV BGR 数组。

    Args:
        serial: 目标设备的 ADB serial。
        adb_path: 显式 ADB 路径；未提供时使用 device 的路径规则。

    Returns:
        OpenCV BGR 排列的 ``uint8`` 截图数组。

    Raises:
        DeviceConnectionError: 设备连接、截图命令或图片解码失败。
        DeviceNotFoundError: 没有找到 ADB 可执行文件。
    """
    executable = find_adb_executable(adb_path)
    connect_adb_device(serial, executable)
    result = _execute_adb_command(
        executable,
        ['-s', serial, 'exec-out', 'screencap', '-p'],
        binary=True,
        timeout=_ADB_COMMAND_TIMEOUT_SECONDS,
    )
    if result.returncode != 0 or not result.stdout:
        detail = result.stderr.decode(errors='replace').strip() if result.stderr else ''
        raise DeviceConnectionError(f'ADB 截图失败: {detail or "没有返回图片"}')

    encoded = numpy.frombuffer(result.stdout, dtype=numpy.uint8)
    screen = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if screen is None:
        raise DeviceConnectionError('ADB 返回的截图不是有效 PNG')
    return screen


def restart_adb_server(adb_path: str | Path | None = None) -> None:
    """重启 ADB server。

    Args:
        adb_path: 显式 ADB 路径；未提供时使用 device 的路径规则。

    Raises:
        DeviceConnectionError: ADB server 启动失败。
        DeviceNotFoundError: 没有找到 ADB 可执行文件。
    """
    executable = find_adb_executable(adb_path)
    _execute_adb_command(executable, ['kill-server'], timeout=_ADB_CONNECT_TIMEOUT_SECONDS)
    time.sleep(_ADB_SERVER_RESTART_DELAY_SECONDS)
    result = _execute_adb_command(
        executable,
        ['start-server'],
        timeout=_ADB_SERVER_START_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise DeviceConnectionError(f'启动 ADB server 失败: {detail}')


def _find_windows_registry_adb_paths() -> list[str]:
    """从 Windows 注册表收集已知模拟器的 ADB 路径。"""
    # Windows 注册表仅在 Windows 自动发现路径中需要。
    import winreg

    candidates: list[str] = []

    # 雷电安装目录通常直接包含 adb.exe。
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\leidian') as key:
            sub_key_name = winreg.EnumKey(key, 0)
            with winreg.OpenKey(key, sub_key_name) as sub:
                install_dir, _ = winreg.QueryValueEx(sub, 'InstallDir')
                candidates.append(os.path.join(install_dir, 'adb.exe'))
    except OSError:
        pass

    # 蓝叠不同版本使用不同的 ADB 文件名。
    for registry_path in (r'SOFTWARE\BlueStacks_nxt_cn', r'SOFTWARE\BlueStacks_nxt'):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as key:
                install_dir, _ = winreg.QueryValueEx(key, 'InstallDir')
                candidates.append(os.path.join(install_dir, 'HD-Adb.exe'))
                break
        except OSError:
            continue

    # MuMu 12 和旧版的 ADB 分别位于 shell 和 nx_main 目录。
    for registry_path, relative_path in (
        (
            r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer-12.0',
            ('shell', 'adb.exe'),
        ),
        (
            r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer',
            ('nx_main', 'adb.exe'),
        ),
    ):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as key:
                uninstall_string, _ = winreg.QueryValueEx(key, 'UninstallString')
                root = os.path.dirname(uninstall_string.strip('"'))
                candidates.append(os.path.join(root, *relative_path))
        except OSError:
            continue

    return candidates


def _execute_adb_command(
    adb_path: Path,
    arguments: Sequence[str],
    *,
    binary: bool = False,
    timeout: float = 10.0,
) -> subprocess.CompletedProcess[Any]:
    """执行一次受控的 ADB 命令。

    Args:
        adb_path: 已由本模块定位的 ADB 可执行文件。
        arguments: 传给 ADB 的命令参数。
        binary: 是否保留标准输出为二进制。
        timeout: 命令最长执行时间，单位为秒。

    Returns:
        ADB 进程结果。

    Raises:
        DeviceConnectionError: ADB 命令超时。
    """
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    try:
        return subprocess.run(  # noqa: S603 - executable path由本模块受控解析。
            [str(adb_path), *arguments],
            capture_output=True,
            check=False,
            creationflags=creation_flags,
            encoding=None if binary else 'utf-8',
            errors=None if binary else 'replace',
            text=not binary,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise DeviceConnectionError(f'ADB 命令超时: {arguments[0]}') from exc


__all__ = [
    'capture_device_screenshot',
    'connect_adb_device',
    'find_adb_executable',
    'read_adb_devices',
    'restart_adb_server',
]
