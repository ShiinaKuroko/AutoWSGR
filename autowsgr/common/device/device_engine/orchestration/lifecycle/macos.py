"""管理 macOS 宿主下的模拟器进程生命周期。

直接调用方：lifecycle 工厂创建的 macOS 模拟器管理器。
下层依赖：设备错误、生命周期抽象、平台类型和 system.logger。
边界：只管理宿主进程，不执行设备内截图或触控操作。
"""

from __future__ import annotations

import json
import os
import subprocess

from autowsgr.common.device.device_engine.foundation.platform import EmulatorType
from autowsgr.common.device.device_engine.orchestration.lifecycle.base import EmulatorProcessManager
from autowsgr.common.device.errors import DeviceError, DeviceNotFoundError
from autowsgr.common.system.logger import get_logger


_log = get_logger('device.lifecycle')


class MacEmulatorManager(EmulatorProcessManager):
    """管理 macOS 宿主上的模拟器进程。"""

    # ── 进程状态 ────────────────────────────────────────────────────────────

    def check_emulator_running(self) -> bool:
        """检查 macOS 宿主上的模拟器是否正在运行。"""
        if not self._process_name:
            return False
        try:
            subprocess.check_output(['pgrep', '-f', self._process_name])  # noqa: S603, S607
        except subprocess.CalledProcessError:
            return False

        # MuMu 进程存在不等于目标实例在线，还需按 ADB 端口复核。
        if self._emulator_type == EmulatorType.mumu:
            mumu_info = self._read_mumu_instance_info()
            port = (self._serial or '').split(':')[-1]
            results = mumu_info.get('return', {}).get('results', [])
            return any(port == v.get('adb_port') for v in results)
        return True

    # ── 进程生命周期 ────────────────────────────────────────────────────────

    def start_emulator(self) -> None:
        """启动模拟器并等待其上线。"""
        if not self._path:
            _log.error(
                "[DEVICE] 模拟器进程 → 拒绝：operation='start', "
                "reason='path_missing', result='failed'",
            )
            raise DeviceNotFoundError('未设置模拟器路径，无法启动')

        try:
            # 1. 启动宿主模拟器进程。
            _log.info('[DEVICE] 模拟器进程 → 启动：路径={!r}', self._path)
            subprocess.Popen(['open', '-a', self._path])  # noqa: S603, S607
            if self._emulator_type == EmulatorType.mumu:
                self._restart_mumu_instance()

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
        if self._emulator_type == EmulatorType.mumu:
            _log.info(
                '[DEVICE] 模拟器进程 → 停止：模拟器=MuMu，结果=跳过，原因=命令行不支持',
            )
            return
        if not self._process_name:
            _log.error(
                "[DEVICE] 模拟器进程 → 拒绝：operation='stop', "
                "reason='process_name_missing', result='failed'",
            )
            raise DeviceError('未设置进程名，无法停止')
        try:
            # 1. 提交宿主终止命令；macOS 的 pkill 由系统异步处理。
            _log.info('[DEVICE] 模拟器进程 → 停止：进程名={!r}', self._process_name)
            subprocess.Popen(['pkill', '-9', '-f', self._process_name])  # noqa: S603, S607
            _log.info('[DEVICE] 模拟器进程 → 停止：结果=已提交')
        except Exception as exc:
            _log.error(
                "[DEVICE] 模拟器进程 → 失败：operation='stop', "
                "process_name={!r}, error_type={!r}, error={!r}, result='failed'",
                self._process_name,
                type(exc).__name__,
                str(exc),
            )
            raise DeviceError(f'停止模拟器失败: {exc}') from exc

    # ── MuMu 实例状态 ──────────────────────────────────────────────────────

    @property
    def _mumu_tool_path(self) -> str:
        """返回 MuMu 管理工具路径。"""
        if not self._path:
            return ''
        return os.path.join(self._path, 'Contents/MacOS/mumutool')

    def _read_mumu_instance_info(self) -> dict:
        """读取 MuMu 实例状态，失败时返回空结果。

        Returns:
            MuMu 管理工具返回的实例信息；工具不可用或内容无效时为空字典。
        """
        tool = self._mumu_tool_path
        if not tool or not os.path.isfile(tool):
            _log.warning(
                "[DEVICE] 模拟器进程 → 查询：emulator='mumu', "
                "reason='tool_missing', result='fallback_empty'",
            )
            return {}
        proc = subprocess.Popen(  # noqa: S603
            [tool, 'info', 'all'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, _ = proc.communicate()
        try:
            return json.loads(out.decode())
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            _log.warning(
                "[DEVICE] 模拟器进程 → 查询：emulator='mumu', "
                "error_type={!r}, error={!r}, result='fallback_empty'",
                type(exc).__name__,
                str(exc),
            )
            return {}

    def _restart_mumu_instance(self) -> None:
        """重启对应 MuMu 实例（通过端口匹配）。"""
        tool = self._mumu_tool_path
        port = (self._serial or '').split(':')[-1]
        info = self._read_mumu_instance_info()
        for idx, v in enumerate(info.get('return', {}).get('results', [])):
            if port == v.get('adb_port'):
                subprocess.Popen(  # noqa: S603
                    [tool, 'restart', str(idx)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                break
