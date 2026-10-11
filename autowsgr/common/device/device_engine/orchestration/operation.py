"""模块功能：编排同一设备会话上的屏幕输入和 Android 应用操作。

上层调用：
- common.device.service：取用点击、滑动、按键和应用操作入口。

下层依赖：
- common.device.device_engine.session：提供 Scrcpy 和 ADB 设备会话。

边界：只转发设备操作，不负责建立或维护连接、不识别游戏页面。
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from autowsgr.common.device.device_engine.session import DeviceSession


def _click_screen(session: DeviceSession, x: float, y: float, *, delay: bool = False) -> None:
    """点击屏幕相对坐标。

    Args:
        session: 当前设备会话。
        x: 横向相对坐标。
        y: 纵向相对坐标。
        delay: 是否在点击前应用配置的随机延迟。
    """
    session.scrcpy.click_screen(x, y, delay=delay)


def _swipe_screen(
    session: DeviceSession,
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
        session: 当前设备会话。
        x1: 起点横向相对坐标。
        y1: 起点纵向相对坐标。
        x2: 终点横向相对坐标。
        y2: 终点纵向相对坐标。
        duration: 手势持续时间，单位为秒。
        delay: 是否在滑动前应用配置的随机延迟。
    """
    session.scrcpy.swipe_screen(x1, y1, x2, y2, duration, delay=delay)


def _long_press_screen(
    session: DeviceSession,
    x: float,
    y: float,
    duration: float = 1.0,
) -> None:
    """在相对坐标处执行长按。

    Args:
        session: 当前设备会话。
        x: 横向相对坐标。
        y: 纵向相对坐标。
        duration: 长按持续时间，单位为秒。
    """
    session.scrcpy.long_press_screen(x, y, duration)


def _send_key_event(session: DeviceSession, key_code: int, *, delay: bool = False) -> None:
    """发送 Android 按键事件。

    Args:
        session: 当前设备会话。
        key_code: Android 按键编码。
        delay: 是否在按键前应用配置的随机延迟。
    """
    session.scrcpy.send_key_event(key_code, delay=delay)


def _input_text(session: DeviceSession, content: str, *, delay: bool = False) -> None:
    """向当前输入目标写入文本。

    Args:
        session: 当前设备会话。
        content: 待输入文本。
        delay: 是否在输入前应用配置的随机延迟。
    """
    session.scrcpy.input_text(content, delay=delay)


def _start_application(session: DeviceSession, package: str) -> None:
    """启动指定的 Android 应用。

    Args:
        session: 当前设备会话。
        package: Android 应用包名。
    """
    session._require_adb_device().app_start(package)


def _stop_application(session: DeviceSession, package: str) -> None:
    """停止指定的 Android 应用。

    Args:
        session: 当前设备会话。
        package: Android 应用包名。
    """
    session._require_adb_device().app_stop(package)


def _check_application_running(session: DeviceSession, package: str) -> bool:
    """检查指定的 Android 应用是否正在运行。

    Args:
        session: 当前设备会话。
        package: Android 应用包名。

    Returns:
        应用进程存在时为 True。
    """
    return package in _execute_shell_command(session, 'ps -A')


def _find_application_display(session: DeviceSession, package: str) -> int | None:
    """查找应用当前前台的显示器编号。

    多显示器模拟器（如 MuMu 的独立屏）会把应用放到非默认显示器上，截图必须跟随，
    否则只能截到默认显示器上的桌面。

    Args:
        session: 当前设备会话。
        package: Android 应用包名。

    Returns:
        应用所在显示器编号；应用不在任何显示器前台时为 None。
    """
    dump = _execute_shell_command(session, 'dumpsys activity activities')
    current_display: int | None = None
    for line in dump.splitlines():
        display_match = re.match(r'\s*Display #(\d+)', line)
        if display_match is not None:
            current_display = int(display_match.group(1))
        if 'topResumedActivity' in line and package in line:
            return current_display
    return None


def _execute_shell_command(session: DeviceSession, cmd: str) -> str:
    """执行设备 Shell 命令并返回标准输出。

    Args:
        session: 当前设备会话。
        cmd: 设备内 Shell 命令。

    Returns:
        命令标准输出文本。
    """
    result = session._require_adb_device().shell(cmd)
    return result if isinstance(result, str) else str(result)
