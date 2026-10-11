"""模块功能：日志基础能力。

创建带通道的日志对象，并初始化控制台和文件输出。

上层调用：
- application、business、dispatch 和 common 内部各模块：用 get_logger 取得模块日志对象。
- 顶层启动流程：用 setup_logger 初始化日志输出。

下层依赖：
- Loguru：日志对象、sink 和格式化的底层实现。
- Python 标准库 logging、sys 和 pathlib。
- common.system.config：提供 LogConfig 和 LOG_TIMEZONE。

边界：不决定业务结果、页面状态、重试策略或业务日志文本。

本模块是日志基础设施，允许格式 bootstrap 例外：sink 使用
`{time} | {level} | {src} | {message}` 输出技术字段，不遵循业务日志的
`[模块名] 位置 → 动作：附加信息` 格式；业务日志文本仍由调用方按该格式书写。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from autowsgr.common.system.config import LOG_TIMEZONE, LogConfig


if TYPE_CHECKING:
    from collections.abc import Callable

    from loguru import Logger


# ── 日志时间与级别 ──────────────────────────────────────────────────────────

# 项目根目录，用于将绝对路径转换为相对路径（Ctrl+点击用）
_PROJECT_ROOT = Path(__file__).resolve().parents[3]

# 项目支持的四种日志级别及其数值。
_LEVEL_MAP: dict[str, int] = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
}


# ── 日志对象 ────────────────────────────────────────────────────────────────


def get_logger(channel: str) -> Logger:
    """创建绑定稳定通道名的日志对象。

    用法：先用 get_logger 取得模块日志对象，再按业务日志格式书写文本，例如
    `_log.info('[COMBAT] 状态机 → 进入战斗：结果={}', result)`。

    Args:
        channel: 调用模块的通道名称，例如 combat 或 vision.pixel。

    Returns:
        带有通道字段的日志对象，可直接调用 debug()、info() 等方法。
    """
    return logger.bind(ch=channel)


# ── 日志输出初始化 ──────────────────────────────────────────────────────────


def setup_logger(config: LogConfig | None = None) -> None:
    """按配置初始化全局日志输出。

    Args:
        config: 已校验的日志配置；省略时使用默认配置。
    """
    config = config or LogConfig()
    log_dir = config.LOG_USER_DIR
    rotation = config.LOG_ROTATION
    retention = config.LOG_RETENTION
    debug_channels = _open_debug_channels(config)

    # 1. 清理旧 sink，避免重复初始化造成重复输出。
    logger.remove()

    # 2. 为每条记录统一补充时区、源码位置和通道字段。
    logger.configure(patcher=_src_patcher)

    sink_format = (
        '<green>{time:HH:mm:ss.SSS}</green> | '
        '<level>{level:8}</level> | '
        '<cyan>{extra[src]}</cyan> | '
        '{message}'
    )

    # 3. 控制台和文件使用同一套级别及 DEBUG 模块筛选。
    console_level_no = _LEVEL_MAP[config.LOG_LEVEL]
    sink_filter = _make_filter(console_level_no, debug_channels)
    logger.add(
        sys.stderr,
        level=0,  # 由 filter 全权控制
        filter=sink_filter,
        format=sink_format,
    )

    # 4. 文件输出使用同一筛选器，并按配置执行切分和保留。
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_dir / 'autowsgr_{time:YYYY-MM-DD}.log',
            level=0,
            filter=sink_filter,
            rotation=rotation,
            retention=retention,
            encoding='utf-8',
            format=sink_format,
        )

    # 5. 降低第三方库的低价值 Python logging 输出。
    for third_party_logger_name in ('adbutils',):
        logging.getLogger(third_party_logger_name).setLevel(logging.WARNING)


# ── 日志记录加工 ────────────────────────────────────────────────────────────


def _src_patcher(record: dict) -> None:
    """为日志记录补充北京时间、源码位置和通道字段。

    Args:
        record: Loguru 提供的当前日志记录。
    """
    # 文件名、正文和目录切分必须使用同一个时区。
    record['time'] = record['time'].astimezone(LOG_TIMEZONE)
    try:
        relative_path = Path(record['file'].path).relative_to(_PROJECT_ROOT)
        # 统一使用正斜杠，便于终端跳转到源码。
        record['extra']['src'] = f'{relative_path.as_posix()}:{record["line"]}'
    except ValueError:
        record['extra']['src'] = f'{record["file"].name}:{record["line"]}'

    # 未绑定通道的调用也必须能安全格式化。
    record['extra'].setdefault('ch', '')


# ── 日志级别筛选 ────────────────────────────────────────────────────────────


def _open_debug_channels(config: LogConfig) -> frozenset[str]:
    """读取配置中已打开的 DEBUG 通道前缀。

    Args:
        config: 已完成字段校验的日志配置。

    Returns:
        已启用的通道前缀集合，例如 LOG_COMBAT_OPEN 对应 combat。
    """
    return frozenset(
        key.removeprefix('LOG_').removesuffix('_OPEN').lower()
        for key, field_value in config.model_dump().items()
        if key.startswith('LOG_') and key.endswith('_OPEN') and field_value
    )


def _make_filter(sink_level: int, debug_channels: frozenset[str]) -> Callable:
    """创建控制台和文件共用的日志筛选器。

    Args:
        sink_level: 普通日志的最低级别数值。
        debug_channels: 允许输出 DEBUG 的通道前缀。

    Returns:
        接收 Loguru 记录并返回是否输出的筛选函数。
    """

    def _filter(record: dict) -> bool:
        level_name = record['level'].name
        # 项目只接收四种级别，其他 Loguru 级别直接丢弃。
        if level_name not in _LEVEL_MAP:
            return False

        if level_name == 'DEBUG':
            # DEBUG 是诊断脚手架，只对明确打开的模块输出。
            channel = str(record['extra'].get('ch', '')).lower()
            return any(
                channel == prefix or channel.startswith(f'{prefix}.') for prefix in debug_channels
            )
        return record['level'].no >= sink_level

    return _filter


__all__ = ['get_logger', 'setup_logger']
