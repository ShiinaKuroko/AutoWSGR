"""管理 Windows 宿主下的模拟器进程生命周期。

直接调用方：lifecycle 工厂创建的 Windows 模拟器管理器。
下层依赖：设备错误、生命周期抽象、平台类型和 system.logger。
边界：只管理宿主进程，不执行设备内截图或触控操作。
"""

from __future__ import annotations

import json
import os
import re
import subprocess

from autowsgr.common.device.device_engine.foundation.platform import EmulatorType
from autowsgr.common.device.device_engine.orchestration.lifecycle.base import EmulatorProcessManager
from autowsgr.common.device.errors import DeviceError, DeviceNotFoundError
from autowsgr.common.system.logger import get_logger


_log = get_logger('device.lifecycle')


class WindowsEmulatorManager(EmulatorProcessManager):
    """管理 Windows 宿主上的模拟器进程。"""

    # ── 进程状态 ────────────────────────────────────────────────────────────

    def check_emulator_running(self) -> bool:
        """检查 Windows 宿主上的模拟器是否正在运行。"""
        match self._emulator_type:
            case EmulatorType.leidian:
                raw = self._execute_ldconsole_command('isrunning')
                running = raw.strip() == 'running'
                _log.debug(
                    "[DEVICE] 模拟器进程 → 状态：emulator='leidian', raw={!r}, result={!r}",
                    raw,
                    running,
                )
                return running
            case EmulatorType.mumu:
                raw = self._execute_mumu_manager_command('is_android_started')
                try:
                    result = json.loads(raw)
                    is_started = result.get('is_android_started', False)
                except (json.JSONDecodeError, KeyError) as exc:
                    _log.warning(
                        "[DEVICE] 模拟器进程 → 状态：emulator='mumu', "
                        "error_type={!r}, error={!r}, result='fallback_false'",
                        type(exc).__name__,
                        str(exc),
                    )
                    is_started = False
                _log.debug(
                    "[DEVICE] 模拟器进程 → 状态：emulator='mumu', result={!r}",
                    bool(is_started),
                )
                return bool(is_started)
            case EmulatorType.yunshouji:
                _log.debug(
                    "[DEVICE] 模拟器进程 → 状态：emulator='yunshouji', result=True, "
                    "reason='always_online'",
                )
                return True  # 云手机始终在线。
            case _:
                return self._check_tasklist_process()

    # ── 进程生命周期 ────────────────────────────────────────────────────────

    def start_emulator(self) -> None:
        """启动模拟器并等待其上线。"""
        if self._emulator_type == EmulatorType.yunshouji:
            _log.info('[DEVICE] 模拟器进程 → 启动：模拟器=云手机，结果=跳过，原因=持续在线')
            return

        if self._path is None:
            _log.error(
                "[DEVICE] 模拟器进程 → 拒绝：operation='start', "
                "reason='path_missing', result='failed'",
            )
            raise DeviceNotFoundError('未设置模拟器路径，无法启动')

        try:
            # 1. 根据模拟器类型选择宿主启动命令。
            _log.info('[DEVICE] 模拟器进程 → 启动：路径={!r}', self._path)
            match self._emulator_type:
                case EmulatorType.leidian:
                    self._execute_ldconsole_command('launch')
                case EmulatorType.mumu:
                    self._execute_mumu_manager_command('launch')
                case _:
                    subprocess.Popen([self._path])  # noqa: S603

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
        if (
            self._emulator_type
            not in {
                EmulatorType.leidian,
                EmulatorType.mumu,
                EmulatorType.yunshouji,
            }
            and not self._process_name
        ):
            _log.error(
                "[DEVICE] 模拟器进程 → 拒绝：operation='stop', "
                "reason='process_name_missing', result='failed'",
            )
            raise DeviceError('未设置进程名，无法停止模拟器')
        if self._emulator_type == EmulatorType.yunshouji:
            _log.info('[DEVICE] 模拟器进程 → 停止：模拟器=云手机，结果=跳过，原因=持续在线')
            return
        try:
            # 1. 根据模拟器类型选择宿主终止命令。
            _log.info('[DEVICE] 模拟器进程 → 停止：模拟器={!r}', self._emulator_type.value)
            match self._emulator_type:
                case EmulatorType.leidian:
                    self._execute_ldconsole_command('quit')
                case EmulatorType.mumu:
                    self._execute_mumu_manager_command('shutdown')
                case _:
                    subprocess.run(  # noqa: S603
                        ['taskkill', '-f', '-im', self._process_name],  # noqa: S607
                        check=True,
                        capture_output=True,
                    )
            _log.info('[DEVICE] 模拟器进程 → 停止：结果=成功')
        except DeviceError:
            raise
        except Exception as exc:
            _log.error(
                "[DEVICE] 模拟器进程 → 失败：operation='stop', "
                "error_type={!r}, error={!r}, result='failed'",
                type(exc).__name__,
                str(exc),
            )
            raise DeviceError(f'停止模拟器失败: {exc}') from exc

    # ── 雷电进程控制 ────────────────────────────────────────────────────────

    def _execute_ldconsole_command(self, command: str, command_arg: str = '') -> str:
        """调用 ldconsole.exe 控制雷电模拟器。"""
        if not self._path:
            raise DeviceNotFoundError('未设置雷电模拟器路径')

        console = os.path.join(os.path.dirname(self._path), 'ldconsole.exe')
        if not os.path.isfile(console):
            raise DeviceNotFoundError(f'找不到 ldconsole.exe: {console}')

        serial = self._serial or 'emulator-5554'
        match = re.search(r'\d+', serial)
        emulator_index = int((int(match.group()) - 5554) / 2) if match else 0

        cmd: list[str] = [console, command, '--index', str(emulator_index)]
        if command_arg:
            cmd.append(command_arg)

        return self._execute_host_command(cmd)

    # ── MuMu 进程控制 ───────────────────────────────────────────────────────

    def _execute_mumu_manager_command(self, command: str, command_arg: str = '') -> str:
        """调用 MuMuManager.exe 控制 MuMu 模拟器。"""
        if not self._path:
            raise DeviceNotFoundError('未设置 MuMu 模拟器路径')

        console = os.path.join(os.path.dirname(self._path), 'MuMuManager.exe')
        if not os.path.isfile(console):
            raise DeviceNotFoundError(f'找不到 MuMuManager.exe: {console}')

        serial = self._serial or '127.0.0.1:16384'
        num_match = re.search(r'[:-]\s*(\d+)', serial)
        if num_match:
            num = int(num_match.group(1))
            emulator_index = (num - 16384) // 32 if num >= 16384 else (num - 5555) // 2
        else:
            emulator_index = 0

        order = 'info' if command == 'is_android_started' else 'control'
        cmd: list[str] = [console, order, '-v', str(emulator_index), command]
        if command_arg:
            cmd.append(command_arg)

        return self._execute_host_command(cmd)

    # ── 通用进程状态 ────────────────────────────────────────────────────────

    def _check_tasklist_process(self) -> bool:
        """通过 tasklist 检查进程是否存在。"""
        if not self._process_name:
            return False
        try:
            raw = subprocess.check_output(  # noqa: S603
                ['tasklist', '/fi', f'ImageName eq {self._process_name}'],  # noqa: S607
            ).decode('gbk', errors='replace')
        except subprocess.CalledProcessError:
            return False
        else:
            return 'PID' in raw

    @staticmethod
    def _execute_host_command(cmd: list[str]) -> str:
        """执行外部命令并返回 stdout。"""
        proc = subprocess.Popen(  # noqa: S603
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = proc.communicate()
        return (
            out.decode('utf-8', errors='replace') if out else err.decode('utf-8', errors='replace')
        )
