"""模块功能：编排宿主模拟器的创建、启停和上线等待。

上层调用：
- common.device.service：取用模拟器启停和上线等待入口。
- common.device.device_engine.session：取用模拟器管理器工厂。

下层依赖：
- common.device.device_engine.orchestration.lifecycle 的各宿主实现、foundation.platform、common.device.config 和 common.device.errors。

边界：不执行 Android 设备内的截图、触控或应用操作。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common.device.device_engine.foundation.platform import (
    OSType,
    detect_host_operating_system,
)
from autowsgr.common.device.device_engine.orchestration.lifecycle.base import EmulatorProcessManager
from autowsgr.common.device.device_engine.orchestration.lifecycle.linux import LinuxEmulatorManager
from autowsgr.common.device.device_engine.orchestration.lifecycle.macos import MacEmulatorManager
from autowsgr.common.device.device_engine.orchestration.lifecycle.windows import (
    WindowsEmulatorManager,
)
from autowsgr.common.device.errors import DeviceError


if TYPE_CHECKING:
    from autowsgr.common.device.config import DeviceConfig
    from autowsgr.common.device.device_engine.session import DeviceSession


def create_emulator_process_manager(
    config: DeviceConfig,
    os_type: OSType | None = None,
    serial: str | None = None,
) -> EmulatorProcessManager:
    """根据宿主操作系统创建模拟器进程管理器。

    Args:
        config: 模拟器类型和宿主程序路径配置。
        os_type: 宿主操作系统类型；未提供时自动检测。
        serial: 已选择的 ADB serial；用于在线状态判断。

    Returns:
        对应操作系统的进程管理器。

    Raises:
        DeviceError: 宿主操作系统不受支持。
    """
    if os_type is None:
        os_type = detect_host_operating_system()

    match os_type:
        case OSType.windows:
            return WindowsEmulatorManager(config, serial)
        case OSType.macos:
            return MacEmulatorManager(config, serial)
        case OSType.linux:
            return LinuxEmulatorManager(config, serial)
        case _:
            raise DeviceError(f'不支持的操作系统: {os_type}')


def _check_emulator_running(session: DeviceSession) -> bool:
    """检查宿主模拟器进程是否正在运行。

    Args:
        session: 当前设备会话。

    Returns:
        模拟器已运行并可被当前宿主检查到时为 True。
    """
    return _ensure_emulator_manager(session).check_emulator_running()


def _start_emulator(session: DeviceSession) -> None:
    """启动宿主模拟器并等待其上线。

    Args:
        session: 当前设备会话。

    Raises:
        DeviceError: 模拟器路径、启动命令或上线等待失败。
    """
    _ensure_emulator_manager(session).start_emulator()


def _stop_emulator(session: DeviceSession) -> None:
    """停止宿主模拟器进程。

    Args:
        session: 当前设备会话。

    Raises:
        DeviceError: 模拟器停止命令失败。
    """
    _ensure_emulator_manager(session).stop_emulator()


def _restart_emulator(session: DeviceSession) -> None:
    """重启宿主模拟器进程。

    Args:
        session: 当前设备会话。

    Raises:
        DeviceError: 模拟器停止或重新启动失败。
    """
    _ensure_emulator_manager(session).restart_emulator()


def _wait_for_emulator_online(session: DeviceSession, timeout: float = 120) -> None:
    """等待宿主模拟器上线。

    Args:
        session: 当前设备会话。
        timeout: 最大等待时间，单位为秒。

    Raises:
        DeviceError: 等待结束时模拟器仍未上线。
    """
    _ensure_emulator_manager(session).wait_for_emulator_online(timeout)


def _ensure_emulator_manager(session: DeviceSession) -> EmulatorProcessManager:
    """返回或创建会话唯一的模拟器生命周期管理器。"""
    if session.lifecycle is None:
        serial = session.serial or session.config.ADB_CONNECTION
        session.lifecycle = create_emulator_process_manager(session.config, serial=serial)
    return session.lifecycle


__all__ = [
    'EmulatorProcessManager',
    'LinuxEmulatorManager',
    'MacEmulatorManager',
    'WindowsEmulatorManager',
    'create_emulator_process_manager',
]
