"""模块功能：读取宿主平台事实并解析模拟器安装信息。

上层调用：
- common.device.config：取用模拟器类型枚举。
- common.device.device_engine.orchestration.discovery 和 lifecycle：取用平台事实与安装路径。

下层依赖：
- common.system.enums：提供宿主系统枚举基类。
- Python 标准库和 Windows 注册表：提供环境与路径探测。

边界：只读取宿主平台事实，不执行模拟器进程控制或 ADB 设备 I/O。
"""

from __future__ import annotations

import os
import sys

from autowsgr.common.system.enums import StrEnum


class OSType(StrEnum):
    """宿主操作系统类型。"""

    windows = 'Windows'
    linux = 'linux'
    macos = 'macOS'


class EmulatorType(StrEnum):
    """Android 模拟器或云手机类型。"""

    leidian = '雷电'
    bluestacks = '蓝叠'
    mumu = 'MuMu'
    yunshouji = '云手机'
    others = '其他'


def detect_host_operating_system() -> OSType:
    """根据当前运行环境返回受支持的宿主系统类型。

    Returns:
        当前宿主系统类型。

    Raises:
        ValueError: 当前宿主系统不受支持，或 Linux 不是 WSL 环境。
    """
    if sys.platform.startswith('win'):
        return OSType.windows
    if sys.platform == 'darwin':
        return OSType.macos
    if sys.platform.startswith('linux'):
        if check_wsl_environment():
            return OSType.linux
        raise ValueError('暂不支持非 WSL 的 Linux 系统')
    raise ValueError(f'不支持的操作系统: {sys.platform}')


def check_wsl_environment() -> bool:
    """判断当前 Linux 环境是否运行在 WSL 中。

    Returns:
        检测到 WSL 环境特征时为 True。
    """
    if os.environ.get('WSL_DISTRO_NAME') or os.environ.get('WSL_INTEROP'):
        return True
    for path in ('/proc/sys/kernel/osrelease', '/proc/version'):
        try:
            with open(path, encoding='utf-8', errors='ignore') as fh:
                if 'microsoft' in fh.read().lower():
                    return True
        except OSError:
            continue
    return False


def calculate_default_emulator_serial(emulator_type: EmulatorType, os_type: OSType) -> str:
    """返回模拟器在指定宿主系统下的默认 ADB serial。

    Args:
        emulator_type: 模拟器类型。
        os_type: 宿主操作系统类型。

    Returns:
        默认 ADB serial。

    Raises:
        ValueError: 没有对应的默认 serial。
    """
    if os_type == OSType.windows:
        match emulator_type:
            case EmulatorType.leidian:
                return 'emulator-5554'
            case EmulatorType.bluestacks:
                return '127.0.0.1:5555'
            case EmulatorType.mumu:
                return '127.0.0.1:16384'
    elif os_type == OSType.macos:
        match emulator_type:
            case EmulatorType.bluestacks | EmulatorType.mumu:
                return '127.0.0.1:5555'
    raise ValueError(f'没有为 {emulator_type.value} 在 {os_type.value} 设置默认 serial')


def resolve_emulator_path(emulator_type: EmulatorType, os_type: OSType) -> str:
    """从宿主系统解析模拟器可执行文件路径。

    Args:
        emulator_type: 模拟器类型。
        os_type: 宿主操作系统类型。

    Returns:
        模拟器可执行文件路径。

    Raises:
        FileNotFoundError: 没有找到模拟器安装路径。
        ValueError: 当前系统或模拟器类型不支持自动解析。
    """
    match os_type:
        case OSType.windows:
            return _resolve_windows_emulator_path(emulator_type)
        case OSType.macos:
            return _resolve_macos_emulator_path(emulator_type)
        case _:
            raise ValueError(f'没有为 {os_type.value} 设置模拟器路径查找方法')


def _resolve_windows_emulator_path(emulator_type: EmulatorType) -> str:
    """从 Windows 注册表解析模拟器安装路径。"""
    # Windows 注册表模块只在实际执行 Windows 路径时加载。
    import winreg

    try:
        match emulator_type:
            case EmulatorType.leidian:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\leidian') as key:
                    sub_key_name = winreg.EnumKey(key, 0)
                    with winreg.OpenKey(key, sub_key_name) as sub:
                        path, _ = winreg.QueryValueEx(sub, 'InstallDir')
                        return os.path.join(path, 'dnplayer.exe')
            case EmulatorType.bluestacks:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r'SOFTWARE\BlueStacks_nxt_cn',
                ) as key:
                    path, _ = winreg.QueryValueEx(key, 'InstallDir')
                    return os.path.join(path, 'HD-Player.exe')
            case EmulatorType.mumu:
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer-12.0',
                    ) as key:
                        path, _ = winreg.QueryValueEx(key, 'UninstallString')
                        return os.path.join(
                            os.path.dirname(path),
                            'shell',
                            'MuMuPlayer.exe',
                        ).strip('"')
                except FileNotFoundError:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer',
                    ) as key:
                        path, _ = winreg.QueryValueEx(key, 'UninstallString')
                        return os.path.join(
                            os.path.dirname(path),
                            'nx_main',
                            'MuMuManager.exe',
                        ).strip('"')
            case _:
                raise ValueError(f'没有为 {emulator_type.value} 设置安装路径查找方法')
    except FileNotFoundError:
        raise FileNotFoundError(f'没有找到 {emulator_type.value} 的安装路径') from None


def _resolve_macos_emulator_path(emulator_type: EmulatorType) -> str:
    """解析 macOS 下的模拟器应用路径。"""
    match emulator_type:
        case EmulatorType.mumu:
            path = '/Applications/MuMuPlayer.app'
        case EmulatorType.bluestacks:
            path = '/Applications/BlueStacks.app'
        case _:
            raise ValueError(f'没有为 {emulator_type.value} 设置安装路径查找方法')

    if os.path.exists(path):
        return path
    home_path = os.path.expanduser(f'~{path}')
    if os.path.exists(home_path):
        return home_path
    raise FileNotFoundError(f'没有找到 {emulator_type.value} 的安装路径')


__all__ = [
    'EmulatorType',
    'OSType',
    'calculate_default_emulator_serial',
    'check_wsl_environment',
    'detect_host_operating_system',
    'resolve_emulator_path',
]
