"""模块功能：持有一次设备连接所需的共享运行状态。

上层调用：
- common.device.device_engine.orchestration.connection、operation 和 screenshot：读写会话事实。
- common.device.device_engine.orchestration.lifecycle.service：读写模拟器管理器。

下层依赖：
- common.device.config、common.device.scrcpy_engine.executor 和生命周期类型。

边界：只持有会话状态，不执行连接流程、不提供业务操作入口。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from autowsgr.common.device.errors import DeviceConnectionError
from autowsgr.common.device.scrcpy_engine import executor


if TYPE_CHECKING:
    from adbutils import AdbDevice

    from autowsgr.common.device.config import DeviceConfig
    from autowsgr.common.device.device_engine.orchestration.lifecycle import EmulatorProcessManager


@dataclass
class DeviceSession:
    """持有单次设备连接的共享状态。"""

    config: DeviceConfig
    serial: str | None = None
    adb_device: AdbDevice | None = None
    scrcpy: executor.ScrcpyEngine = field(init=False)
    lifecycle: EmulatorProcessManager | None = None

    def __post_init__(self) -> None:
        """创建当前会话唯一的 Scrcpy 执行器。"""
        self.scrcpy = executor.ScrcpyEngine(self.config)

    def _require_adb_device(self) -> AdbDevice:
        """返回当前会话的 ADB 设备。

        Returns:
            已建立连接的 ADB 设备对象。

        Raises:
            DeviceConnectionError: 当前会话尚未建立 ADB 连接。
        """
        if self.adb_device is None:
            raise DeviceConnectionError('设备未连接，请先调用 device.service.connect()')
        return self.adb_device
