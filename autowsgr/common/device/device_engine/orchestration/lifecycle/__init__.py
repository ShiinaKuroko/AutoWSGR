"""宿主模拟器生命周期能力出口。"""

from autowsgr.common.device.device_engine.orchestration.lifecycle import service
from autowsgr.common.device.device_engine.orchestration.lifecycle.base import EmulatorProcessManager
from autowsgr.common.device.device_engine.orchestration.lifecycle.linux import LinuxEmulatorManager
from autowsgr.common.device.device_engine.orchestration.lifecycle.macos import MacEmulatorManager
from autowsgr.common.device.device_engine.orchestration.lifecycle.service import (
    create_emulator_process_manager,
)
from autowsgr.common.device.device_engine.orchestration.lifecycle.windows import (
    WindowsEmulatorManager,
)


__all__ = [
    'EmulatorProcessManager',
    'LinuxEmulatorManager',
    'MacEmulatorManager',
    'WindowsEmulatorManager',
    'create_emulator_process_manager',
    'service',
]
