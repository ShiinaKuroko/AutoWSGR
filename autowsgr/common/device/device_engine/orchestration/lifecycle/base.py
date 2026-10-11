"""模块功能：定义宿主模拟器进程生命周期的抽象契约。

上层调用：
- common.device.device_engine.orchestration.lifecycle：通过包出口导出管理器类型。
- linux、macos 和 windows 管理器：实现这些抽象方法。

下层依赖：
- common.device.config、common.device.errors 和 common.system.logger。

边界：只定义宿主进程生命周期，不执行 Android 设备 I/O。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from autowsgr.common.device.errors import DeviceError
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from autowsgr.common.device.config import DeviceConfig


_log = get_logger('device.lifecycle')


_EMULATOR_STATUS_POLL_INTERVAL_SECONDS = 1.0


class EmulatorProcessManager(ABC):
    """定义宿主模拟器进程的启动、停止和在线检查能力。

    Args:
        config: 包含模拟器类型和宿主程序路径的配置。
        serial: 已选择的 ADB serial，用于在线状态判断。
    """

    def __init__(self, config: DeviceConfig, serial: str | None = None) -> None:
        self._config = config
        self._emulator_type = config.DEVICE_EMULATOR_TYPE
        self._path = config.DEVICE_EMULATOR_PATH
        self._process_name = Path(self._path).name if self._path else None
        self._serial = serial

    # ── 进程生命周期 ────────────────────────────────────────────────────────

    @abstractmethod
    def check_emulator_running(self) -> bool:
        """检查模拟器进程是否正在运行。

        Returns:
            模拟器已运行时为 True。
        """
        ...

    @abstractmethod
    def start_emulator(self) -> None:
        """启动模拟器进程。

        Raises:
            DeviceError: 模拟器启动失败。
        """
        ...

    @abstractmethod
    def stop_emulator(self) -> None:
        """停止模拟器进程。

        Raises:
            DeviceError: 模拟器停止失败。
        """
        ...

    def restart_emulator(self) -> None:
        """停止后重新启动模拟器进程。"""
        self.stop_emulator()
        self.start_emulator()

    def wait_for_emulator_online(self, timeout: float = 120) -> None:
        """阻塞等待模拟器上线。

        Args:
            timeout: 最大等待时间，单位为秒。

        Raises:
            DeviceError: 等待结束时模拟器仍未上线。
        """
        start_time = time.monotonic()
        while not self.check_emulator_running():
            if time.monotonic() - start_time > timeout:
                _log.error(
                    '[DEVICE] 模拟器进程 → 超时：等待={}秒，结果=失败，后续=检查宿主进程',
                    timeout,
                )
                raise DeviceError(f'模拟器启动超时 ({timeout}s)')
            time.sleep(_EMULATOR_STATUS_POLL_INTERVAL_SECONDS)
