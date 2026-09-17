"""发现在线设备候选并解析目标设备 serial。

直接调用方：device_engine 的设备连接流程。
下层依赖：ADB 执行器、宿主平台事实、设备配置和设备错误。
边界：不执行原始 ADB 命令、不管理宿主进程、不建立 Android I/O 通道。
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from autowsgr.common.device.adb_engine import executor
from autowsgr.common.device.device_engine.foundation.platform import EmulatorType
from autowsgr.common.device.errors import DeviceConnectionError
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from pathlib import Path

    from autowsgr.common.device.config import DeviceConfig


_log = get_logger('device.discovery')


# ── serial 识别规则 ─────────────────────────────────────────────────────────
_EMULATOR_SERIAL_RULES: list[tuple[re.Pattern[str], EmulatorType]] = [
    (re.compile(r'^emulator-\d+$'), EmulatorType.leidian),
    (re.compile(r'^127\.0\.0\.1:(1638[4-9]|16[4-9]\d{2}|1[7-9]\d{3})$'), EmulatorType.mumu),
    (re.compile(r'^127\.0\.0\.1:620\d{2}$'), EmulatorType.mumu),
    (re.compile(r'^127\.0\.0\.1:5(5[5-9]\d|[6-9]\d{2})\d?$'), EmulatorType.bluestacks),
    (re.compile(r'^127\.0\.0\.1:555[5-9]$'), EmulatorType.bluestacks),
]


@dataclass
class EmulatorCandidate:
    """表示一个已发现的 Android 设备候选。"""

    serial: str
    emulator_type: EmulatorType | None
    status: str
    description: str = field(init=False)

    def __post_init__(self) -> None:
        """生成供交互选择显示的设备描述。"""
        type_label = self.emulator_type.value if self.emulator_type else '未知'
        self.description = f'{self.serial:<25} {type_label:<8} ({self.status})'


# ── 模拟器候选发现 ──────────────────────────────────────────────────────────


def recognize_emulator_type(serial: str) -> EmulatorType | None:
    """根据 serial 格式识别模拟器类型。

    Args:
        serial: ADB serial 字符串。

    Returns:
        识别出的模拟器类型；无法识别时返回 None。
    """
    for pattern, emulator_type in _EMULATOR_SERIAL_RULES:
        if pattern.match(serial):
            return emulator_type
    return None


def discover_emulator_candidates(adb_path: str | Path | None = None) -> list[EmulatorCandidate]:
    """发现当前在线的 Android 设备候选。

    Args:
        adb_path: 显式 ADB 路径；未提供时使用 ADB 执行器的路径规则。

    Returns:
        仅包含 status 为 device 的候选，并按 serial 排序。

    Raises:
        DeviceConnectionError: ADB 设备列表读取失败。
    """
    candidates: list[EmulatorCandidate] = []
    for serial, status in executor.read_adb_devices(adb_path):
        emulator_type = recognize_emulator_type(serial)
        candidate = EmulatorCandidate(serial, emulator_type, status)
        if status == 'device':
            candidates.append(candidate)
            continue
        _log.debug(
            "[DEVICE] 设备发现 → 过滤：serial={!r}, status={!r}, result='skipped'",
            serial,
            status,
        )

    _log.debug(
        "[DEVICE] 设备发现 → 完成：online_count={}, result='checked'",
        len(candidates),
    )
    return sorted(candidates, key=lambda candidate: candidate.serial)


# ── TCP 设备发现 ────────────────────────────────────────────────────────────
_KNOWN_ADB_CONNECTIONS = ('127.0.0.1:16384', '127.0.0.1:62001')


def discover_known_adb_devices() -> list[tuple[str, str]]:
    """连接已知 TCP serial 后读取设备列表。

    Returns:
        设备的 (serial, status) 列表。

    Raises:
        DeviceConnectionError: ADB 路径或设备列表读取失败。
    """
    adb_path = executor.find_adb_executable()
    for serial in _KNOWN_ADB_CONNECTIONS:
        try:
            executor.connect_adb_device(serial, adb_path)
        except DeviceConnectionError as exc:
            _log.debug(
                "[DEVICE] 设备发现 → 连接：serial={!r}, error={!r}, result='continued'",
                serial,
                str(exc),
            )

    devices = executor.read_adb_devices(adb_path)
    _log.info('[DEVICE] 设备发现 → 完成：设备数={}，结果=成功', len(devices))
    return devices


# ── 候选选择 ─────────────────────────────────────────────────────────────────


def select_emulator_candidate(candidates: list[EmulatorCandidate]) -> str:
    """通过命令行从多个设备候选中选择一个。

    Args:
        candidates: 待选择的设备候选列表。

    Returns:
        用户选择的设备 serial。

    Raises:
        DeviceConnectionError: 当前环境无法交互或用户取消选择。
    """
    if not candidates:
        raise DeviceConnectionError('没有可供选择的在线设备')

    if not sys.stdin.isatty():
        serials = ', '.join(candidate.serial for candidate in candidates)
        raise DeviceConnectionError(
            f'检测到多个在线设备（{serials}），无法自动选择；请设置 ADB_CONNECTION。'
        )

    print('\n检测到多个在线设备，请选择要连接的模拟器：\n')  # noqa: T201
    for index, candidate in enumerate(candidates):
        print(f'  [{index}] {candidate.description}')  # noqa: T201
    print()  # noqa: T201

    while True:
        try:
            raw = input(f'请输入编号 [0-{len(candidates) - 1}]: ').strip()
        except (EOFError, KeyboardInterrupt) as exc:
            raise DeviceConnectionError('用户取消了设备选择') from exc

        if raw.isdigit() and 0 <= int(raw) < len(candidates):
            chosen = candidates[int(raw)]
            _log.info('[DEVICE] 设备发现 → 选择：序列号={!r}，结果=成功', chosen.serial)
            return chosen.serial

        print(f'  无效输入，请输入 0 到 {len(candidates) - 1} 之间的整数。')  # noqa: T201


# ── serial 解析 ──────────────────────────────────────────────────────────────


def resolve_device_serial(
    config: DeviceConfig | None = None,
    adb_path: str | Path | None = None,
) -> str:
    """根据配置和在线候选确定目标 serial。

    Args:
        config: 设备配置；为空时仅使用在线候选。
        adb_path: 显式 ADB 路径；未提供时使用自动检测的 ADB。

    Returns:
        最终选择的 ADB serial。

    Raises:
        DeviceConnectionError: 没有在线设备或无法安全选择设备。
    """
    if config is not None and config.ADB_CONNECTION:
        _log.debug(
            '[DEVICE] 设备发现 → 选择：source={!r}, serial={!r}',
            'config',
            config.ADB_CONNECTION,
        )
        return config.ADB_CONNECTION

    candidates = discover_emulator_candidates(adb_path)
    if not candidates:
        raise DeviceConnectionError('未检测到任何在线 Android 设备，请检查模拟器和 ADB 状态。')

    if len(candidates) == 1:
        serial = candidates[0].serial
        _log.info('[DEVICE] 设备发现 → 选择：来源=唯一在线设备，序列号={!r}，结果=成功', serial)
        return serial

    if config is not None:
        matched = [
            candidate
            for candidate in candidates
            if candidate.emulator_type == config.DEVICE_EMULATOR_TYPE
        ]
        if len(matched) == 1:
            serial = matched[0].serial
            _log.info(
                '[DEVICE] 设备发现 → 选择：来源=模拟器类型匹配，序列号={!r}，结果=成功',
                serial,
            )
            return serial
        if matched:
            return select_emulator_candidate(matched)

    return select_emulator_candidate(candidates)


__all__ = [
    'EmulatorCandidate',
    'discover_emulator_candidates',
    'discover_known_adb_devices',
    'recognize_emulator_type',
    'resolve_device_serial',
    'select_emulator_candidate',
]
