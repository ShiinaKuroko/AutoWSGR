"""统一配置模型。

当前配置包含日志能力的 `LOG_` 字段；新增能力配置时，必须使用所属模块前缀。
下层依赖：Pydantic 提供字段校验和不可变模型。
边界：只保存配置值，不读取用户文件，不执行日志或文件操作。
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, model_validator


# 日志目录使用固定的北京时间，不随运行主机的时区变化。
_BEIJING_TIMEZONE = datetime.timezone(datetime.timedelta(hours=8), name='Asia/Shanghai')


class LogConfig(BaseModel):
    """保存日志能力的可覆盖配置。"""

    model_config = {'frozen': True, 'extra': 'forbid'}

    LOG_LEVEL: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'DEBUG'
    """控制普通日志的最低输出级别。"""
    LOG_SYSTEM_DIR: Path = Path('logs')
    """未指定用户目录时使用的日志根目录。"""
    LOG_USER_DIR: Path | None = None
    """用户指定的日志目录；为空时由系统目录和北京时间生成。"""
    LOG_ROTATION: str = '10 MB'
    """单个日志文件达到该大小后切分。"""
    LOG_RETENTION: str = '7 days'
    """日志文件的保留周期，由文件 sink 执行清理。"""
    LOG_COMBAT_OPEN: bool = False
    """是否放行 `combat` 及其子通道的 DEBUG 日志。"""

    @model_validator(mode='after')
    def _set_log_user_dir(self) -> LogConfig:
        """为未指定目录的配置生成按北京时间命名的日志目录。"""
        if self.LOG_USER_DIR is None:
            timestamp = datetime.datetime.now(tz=_BEIJING_TIMEZONE).strftime('%Y-%m-%d_%H-%M-%S')
            object.__setattr__(self, 'LOG_USER_DIR', self.LOG_SYSTEM_DIR / timestamp)
        return self


__all__ = ['LogConfig']
