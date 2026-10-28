"""模块功能：宿主模拟器生命周期能力出口。

上层调用：
- common.device.device_engine.session 和 common.device.service：取用模拟器管理器与工厂。

下层依赖：
- common.device.device_engine.orchestration.lifecycle 的 base、service 和各宿主实现。

只导出工厂和管理器类型，不实现进程控制。
"""

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
