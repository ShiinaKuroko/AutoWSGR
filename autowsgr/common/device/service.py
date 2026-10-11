"""提供设备连接、输入、截图和模拟器维护的统一服务入口。

直接调用方：需要使用设备基础能力的应用、业务和工具模块。
下层依赖：device_engine 流程、DeviceSession、设备配置和 system.files。
边界：只提供设备能力入口，不识别页面、不编排业务任务、不持有业务状态。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.common.device.config import DeviceConfig
from autowsgr.common.device.device_engine import session
from autowsgr.common.device.device_engine.orchestration import (
    connection,
    lifecycle,
    operation,
    screenshot,
)
from autowsgr.common.device.device_engine.orchestration.connection import DeviceInfo


# 等待应用出现在某块显示器上的超时与轮询间隔，单位为秒。
_APPLICATION_DISPLAY_TIMEOUT_SECONDS = 15.0
_APPLICATION_DISPLAY_POLL_SECONDS = 0.5


if TYPE_CHECKING:
    from pathlib import Path

    import numpy


class DeviceService:
    """持有一个设备会话并提供四类设备基础能力。"""

    def __init__(self, config: DeviceConfig | None = None) -> None:
        """创建一个独立的设备会话。

        Args:
            config: 设备、Scrcpy 和操作时序配置；省略时使用默认配置。
        """
        self._session = session.DeviceSession(config or DeviceConfig())

    # ── 连接模拟器 ─────────────────────────────────────────────────────────

    def connect(self, package: str | None = None) -> DeviceInfo:
        """连接设备并完成 ADB、Scrcpy、视频和控制通道初始化。

        Args:
            package: 已知的主应用包名；给出时会跟随它所在的显示器。

        Returns:
            已建立连接的 serial 和设备分辨率。

        Raises:
            DeviceConnectionError: 设备发现、ADB 或 Scrcpy 连接失败。
        """
        info = connection._connect_device(self._session)
        if package is not None:
            self.follow_display(package)
        return info

    # ── 操作模拟器 ─────────────────────────────────────────────────────────

    def click(self, x: float, y: float, *, delay: bool = False) -> None:
        """点击屏幕相对坐标。

        Args:
            x: 横向相对坐标。
            y: 纵向相对坐标。
            delay: 是否在点击前应用配置的随机延迟。
        """
        operation._click_screen(self._session, x, y, delay=delay)

    def swipe(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        duration: float = 0.5,
        *,
        delay: bool = False,
    ) -> None:
        """在两个相对坐标之间执行滑动。

        Args:
            x1: 起点横向相对坐标。
            y1: 起点纵向相对坐标。
            x2: 终点横向相对坐标。
            y2: 终点纵向相对坐标。
            duration: 手势持续时间，单位为秒。
            delay: 是否在滑动前应用配置的随机延迟。
        """
        operation._swipe_screen(self._session, x1, y1, x2, y2, duration, delay=delay)

    def long_tap(self, x: float, y: float, duration: float = 1.0) -> None:
        """在相对坐标处执行长按。

        Args:
            x: 横向相对坐标。
            y: 纵向相对坐标。
            duration: 长按持续时间，单位为秒。
        """
        operation._long_press_screen(self._session, x, y, duration)

    def key_event(self, key_code: int, *, delay: bool = False) -> None:
        """发送 Android 按键事件。

        Args:
            key_code: Android 按键编码。
            delay: 是否在按键前应用配置的随机延迟。
        """
        operation._send_key_event(self._session, key_code, delay=delay)

    def text(self, content: str, *, delay: bool = False) -> None:
        """向当前输入目标写入文本。

        Args:
            content: 待输入文本。
            delay: 是否在输入前应用配置的随机延迟。
        """
        operation._input_text(self._session, content, delay=delay)

    def start_app(self, package: str) -> None:
        """启动指定的 Android 应用，并让截图跟随它所在的显示器。

        Args:
            package: Android 应用包名。
        """
        operation._start_application(self._session, package)
        self.follow_display(package)

    def follow_display(self, package: str) -> None:
        """让截图目标跟随应用所在的显示器。

        多显示器模拟器（如 MuMu 的独立屏）会把应用放到非默认显示器上，而 scrcpy 默认只镜像
        0 号屏；不跟随就只能截到桌面。应用刚启动时那块屏还没建立，因此这里轮询等待。

        Args:
            package: Android 应用包名。
        """
        deadline = time.monotonic() + _APPLICATION_DISPLAY_TIMEOUT_SECONDS
        while True:
            display_id = operation._find_application_display(self._session, package)
            if display_id is not None:
                self._session.scrcpy.reconnect_to_display(display_id)
                return
            if time.monotonic() >= deadline:
                return
            time.sleep(_APPLICATION_DISPLAY_POLL_SECONDS)

    def stop_app(self, package: str) -> None:
        """停止指定的 Android 应用。

        Args:
            package: Android 应用包名。
        """
        operation._stop_application(self._session, package)

    def is_app_running(self, package: str) -> bool:
        """检查指定的 Android 应用是否正在运行。

        Args:
            package: Android 应用包名。

        Returns:
            应用进程存在时为 True。
        """
        return operation._check_application_running(self._session, package)

    def shell(self, cmd: str) -> str:
        """执行设备 Shell 命令并返回标准输出。

        Args:
            cmd: 设备内 Shell 命令。

        Returns:
            命令标准输出文本。
        """
        return operation._execute_shell_command(self._session, cmd)

    # ── 截图与保存 ─────────────────────────────────────────────────────────

    @property
    def resolution(self) -> tuple[int, int]:
        """返回当前设备分辨率，格式为宽度和高度。"""
        return self._session.scrcpy.resolution

    def screenshot(self) -> numpy.ndarray:
        """获取当前 RGB 截图。

        Returns:
            当前视频帧的 RGB 数组。
        """
        return screenshot._capture_device_screenshot(self._session)

    def save_screenshot(
        self,
        path: str | Path,
        *,
        allowed_root: str | Path,
    ) -> None:
        """获取截图并保存到允许目录内。

        Args:
            path: 目标图像路径。
            allowed_root: 允许写入的根目录。
        """
        screenshot._save_device_screenshot(self._session, path, allowed_root=allowed_root)

    # ── 连接维护 ─────────────────────────────────────────────────────────

    def is_connected(self) -> bool:
        """返回设备的 Scrcpy 通道是否已建立。

        Returns:
            Scrcpy 视频和控制通道均可用时为 True。
        """
        return connection._is_device_connected(self._session)

    def disconnect(self) -> None:
        """断开设备连接并释放所有控制资源。"""
        connection._disconnect_device(self._session)

    def reconnect(self) -> DeviceInfo:
        """重新建立完整设备连接。

        Returns:
            重新建立连接后的 serial 和设备分辨率。
        """
        return connection._reconnect_device(self._session)

    def is_emulator_running(self) -> bool:
        """检查宿主模拟器进程是否正在运行。

        Returns:
            模拟器进程已运行时为 True。
        """
        return lifecycle.service._check_emulator_running(self._session)

    def start_emulator(self) -> None:
        """启动宿主模拟器并等待上线。

        Raises:
            DeviceError: 模拟器路径、启动命令或上线等待失败。
        """
        lifecycle.service._start_emulator(self._session)

    def stop_emulator(self) -> None:
        """停止宿主模拟器进程。

        Raises:
            DeviceError: 模拟器停止命令失败。
        """
        lifecycle.service._stop_emulator(self._session)

    def restart_emulator(self) -> None:
        """重启宿主模拟器进程。

        Raises:
            DeviceError: 模拟器停止或重新启动失败。
        """
        lifecycle.service._restart_emulator(self._session)

    def wait_emulator_online(self, timeout: float = 120) -> None:
        """等待宿主模拟器上线。

        Args:
            timeout: 最大等待时间，单位为秒。

        Raises:
            DeviceError: 等待结束时模拟器仍未上线。
        """
        lifecycle.service._wait_for_emulator_online(self._session, timeout)


__all__ = ['DeviceInfo', 'DeviceService']
