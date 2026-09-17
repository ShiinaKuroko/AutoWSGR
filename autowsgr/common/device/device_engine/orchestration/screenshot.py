"""编排设备截图读取和受限路径保存。

直接调用方：device.service 的截图入口。
下层依赖：DeviceSession、Scrcpy 执行器和 system.files。
边界：不负责设备连接、图像识别或截图业务命名。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common.system import files


if TYPE_CHECKING:
    from pathlib import Path

    import numpy

    from autowsgr.common.device.device_engine.session import DeviceSession


def _capture_device_screenshot(session: DeviceSession) -> numpy.ndarray:
    """获取当前 RGB 截图。

    Args:
        session: 当前设备会话。

    Returns:
        当前视频帧的 RGB 数组。
    """
    return session.scrcpy.capture_screenshot()


def _save_device_screenshot(
    session: DeviceSession,
    path: str | Path,
    *,
    allowed_root: str | Path,
) -> None:
    """获取截图并保存到允许目录内。

    Args:
        session: 当前设备会话。
        path: 目标图像路径。
        allowed_root: 允许写入的根目录。
    """
    files.save_image(
        _capture_device_screenshot(session),
        path,
        allowed_root=allowed_root,
    )
