"""编排设备连接和断开流程。

直接调用方：device.service 的设备连接维护入口。
下层依赖：DeviceSession、ADB 执行器、设备发现和 Scrcpy 执行器。
边界：只编排设备连接通道，不执行设备操作、不保存截图、不管理宿主模拟器进程。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from autowsgr.common.device.adb_engine import executor
from autowsgr.common.device.device_engine.orchestration import discovery
from autowsgr.common.device.errors import DeviceConnectionError
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from adbutils import AdbDevice

    from autowsgr.common.device.device_engine.session import DeviceSession


_log = get_logger('device.connection')


# ── 连接流程参数 ────────────────────────────────────────────────────────────

_ADB_CONNECTION_MAX_ATTEMPTS = 3
_ADB_CONNECTION_RETRY_DELAY_SECONDS = 2.0


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """已建立设备连接的基本信息。"""

    serial: str
    resolution: tuple[int, int]


def _connect_device(session: DeviceSession) -> DeviceInfo:
    """完成设备选择、ADB 连接和 Scrcpy 首帧初始化。

    Args:
        session: 当前设备会话。

    Returns:
        已建立连接的 serial 和设备分辨率。

    Raises:
        DeviceConnectionError: ADB、Scrcpy 或首帧初始化失败。
    """
    if session.scrcpy.is_scrcpy_connected():
        return DeviceInfo(session.serial or '', session.scrcpy.resolution)

    serial = discovery.resolve_device_serial(session.config)
    adb_device = _connect_adb_device(serial)
    try:
        resolution = session.scrcpy.connect_scrcpy(adb_device, serial)
    except Exception:
        session.adb_device = None
        raise

    session.adb_device = adb_device
    session.serial = serial
    _log.info(
        '[DEVICE] 设备连接 → 建立：序列号={!r}，分辨率=({}, {})，结果=成功',
        serial,
        *resolution,
    )
    return DeviceInfo(serial, resolution)


def _disconnect_device(session: DeviceSession) -> None:
    """关闭 Scrcpy 通道并释放 ADB 会话引用。

    Args:
        session: 当前设备会话。
    """
    serial = session.serial or '未连接'
    session.scrcpy.disconnect_scrcpy()
    session.adb_device = None
    session.serial = None
    _log.info('[DEVICE] 设备连接 → 断开：序列号={!r}，结果=成功', serial)


def _is_device_connected(session: DeviceSession) -> bool:
    """返回设备的 Scrcpy 通道是否已建立。

    Args:
        session: 当前设备会话。

    Returns:
        Scrcpy 视频和控制通道均可用时为 True。
    """
    return session.scrcpy.is_scrcpy_connected()


def _reconnect_device(session: DeviceSession) -> DeviceInfo:
    """关闭当前连接并重新建立完整设备连接。

    Args:
        session: 当前设备会话。

    Returns:
        重新建立连接后的 serial 和设备分辨率。
    """
    _disconnect_device(session)
    return _connect_device(session)


def _connect_adb_device(serial: str) -> AdbDevice:
    """通过 ADB 执行器建立 adbutils 设备对象。

    Args:
        serial: 目标设备的 ADB serial。

    Returns:
        已连接的 adbutils 设备对象。

    Raises:
        DeviceConnectionError: 多次连接仍未建立可用设备对象。
    """
    # adbutils 设备对象的创建和 ADB 连接必须使用同一个重试边界。
    import adbutils

    last_error: Exception | None = None
    for attempt in range(1, _ADB_CONNECTION_MAX_ATTEMPTS + 1):
        try:
            executor.connect_adb_device(serial)
            return adbutils.adb.device(serial=serial)
        except Exception as exc:
            last_error = exc
            if attempt < _ADB_CONNECTION_MAX_ATTEMPTS:
                _log.debug(
                    '[DEVICE] ADB 连接 → 重试：attempt={}, max_attempts={}, error_type={!r}',
                    attempt,
                    _ADB_CONNECTION_MAX_ATTEMPTS,
                    type(exc).__name__,
                )
                try:
                    executor.restart_adb_server()
                except Exception as restart_error:
                    _log.debug(
                        '[DEVICE] ADB 服务 → 重启：error_type={!r}, result={!r}',
                        type(restart_error).__name__,
                        'continued',
                    )
                time.sleep(_ADB_CONNECTION_RETRY_DELAY_SECONDS)

    _log.error(
        '[DEVICE] 设备连接 → 失败：序列号={!r}，attempts={}，error_type={!r}，结果=失败，后续=终止',
        serial,
        _ADB_CONNECTION_MAX_ATTEMPTS,
        type(last_error).__name__ if last_error else 'UnknownError',
    )
    raise DeviceConnectionError(f'连接设备失败: {serial}') from last_error


__all__ = ['DeviceInfo']
