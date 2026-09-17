"""管理 Linux/WSL 宿主下的模拟器进程生命周期。

直接调用方：lifecycle 工厂创建的 Linux 模拟器管理器。
下层依赖：ADB 执行器、设备错误、生命周期抽象、平台事实和 system.logger。
边界：只管理宿主进程，不执行设备内截图或触控操作。
"""

from __future__ import annotations

import shlex
import subprocess
from typing import TYPE_CHECKING

from autowsgr.common.device.adb_engine import executor
from autowsgr.common.device.device_engine.foundation.platform import check_wsl_environment
from autowsgr.common.device.device_engine.orchestration.lifecycle.base import EmulatorProcessManager
from autowsgr.common.device.errors import DeviceError, DeviceNotFoundError
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from autowsgr.common.device.config import DeviceConfig


_log = get_logger('device.lifecycle')


class LinuxEmulatorManager(EmulatorProcessManager):
    """管理 Linux/WSL 宿主上的模拟器进程。"""

    def __init__(self, config: DeviceConfig, serial: str | None = None) -> None:
        super().__init__(config, serial)
        self._is_wsl = check_wsl_environment()

    # ── 进程状态 ────────────────────────────────────────────────────────────

    def check_emulator_running(self) -> bool:
        """检查 Linux/WSL 宿主上的模拟器是否正在运行。"""
        # 1. ADB 已上线时，直接认为模拟器可用。
        if self._serial and self._serial in self._read_online_adb_serials():
            return True

        # 2. WSL 通过 Windows 进程名检查宿主模拟器。
        if self._is_wsl:
            return self._check_windows_process_running()

        # 3. 原生 Linux 没有进程名时无法判断宿主进程状态。
        if not self._process_name:
            return False
        try:
            subprocess.run(  # noqa: S603
                ['pgrep', '-f', self._process_name],  # noqa: S607
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    # ── 进程生命周期 ────────────────────────────────────────────────────────

    def start_emulator(self) -> None:
        """启动模拟器并等待其上线。"""
        if not self._path:
            _log.error(
                "[DEVICE] 模拟器进程 → 拒绝：operation='start', "
                "reason='path_missing', result='failed'",
            )
            raise DeviceNotFoundError('未设置模拟器路径（WSL 需要显式设置）')
        try:
            # 1. 启动宿主模拟器进程。
            _log.info('[DEVICE] 模拟器进程 → 启动：路径={!r}', self._path)
            subprocess.Popen(shlex.split(self._path))  # noqa: S603

            # 2. 等待 ADB 上线，确认模拟器已经可用。
            self.wait_for_emulator_online()
            _log.info('[DEVICE] 模拟器进程 → 启动：结果=成功')
        except DeviceError:
            raise
        except Exception as exc:
            _log.error(
                "[DEVICE] 模拟器进程 → 失败：operation='start', "
                "error_type={!r}, error={!r}, result='failed'",
                type(exc).__name__,
                str(exc),
            )
            raise DeviceError(f'启动模拟器失败: {exc}') from exc

    def stop_emulator(self) -> None:
        """停止模拟器进程。"""
        if not self._process_name:
            _log.error(
                "[DEVICE] 模拟器进程 → 拒绝：operation='stop', "
                "reason='process_name_missing', result='failed'",
            )
            raise DeviceError('未设置进程名，无法停止模拟器')
        error_msg = ''
        try:
            # 1. 按宿主环境选择终止命令。
            _log.info('[DEVICE] 模拟器进程 → 停止：进程名={!r}', self._process_name)
            if self._is_wsl:
                result = subprocess.run(  # noqa: S603
                    ['taskkill.exe', '/f', '/im', self._process_name],  # noqa: S607
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    error_msg = result.stderr.strip() or result.stdout.strip()
            else:
                subprocess.run(  # noqa: S603
                    ['pkill', '-9', '-f', self._process_name],  # noqa: S607
                    check=True,
                )

            # WSL 的 taskkill 需要检查返回文本，原生 Linux 的 pkill 由 check=True 校验。
        except DeviceError:
            raise
        except Exception as exc:
            _log.error(
                "[DEVICE] 模拟器进程 → 失败：operation='stop', "
                "process_name={!r}, error_type={!r}, error={!r}, result='failed'",
                self._process_name,
                type(exc).__name__,
                str(exc),
            )
            raise DeviceError(f'停止模拟器失败: {exc}') from exc

        if error_msg:
            _log.error(
                "[DEVICE] 模拟器进程 → 失败：operation='stop', "
                "process_name={!r}, error={!r}, result='failed'",
                self._process_name,
                error_msg,
            )
            raise DeviceError(error_msg)
        _log.info(
            '[DEVICE] 模拟器进程 → 停止：进程名={!r}，结果=成功',
            self._process_name,
        )

    # ── 进程状态查询 ─────────────────────────────────────────────────────────

    @staticmethod
    def _read_online_adb_serials() -> list[str]:
        """读取当前处于在线状态的 ADB serial。"""
        try:
            devices = executor.read_adb_devices()
        except DeviceError as exc:
            _log.warning(
                '[DEVICE] 模拟器进程 → ADB 查询：error_type={!r}, error={!r}, '
                "result='fallback_empty'",
                type(exc).__name__,
                str(exc),
            )
            return []

        return [serial for serial, status in devices if status == 'device']

    def _check_windows_process_running(self) -> bool:
        """WSL 下通过 tasklist.exe 检查 Windows 进程。"""
        if not self._process_name:
            return False
        result = subprocess.run(  # noqa: S603
            ['tasklist.exe', '/fi', f'IMAGENAME eq {self._process_name}'],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout or '').lower()
        if 'no tasks' in output:
            return False
        return self._process_name.lower() in output
