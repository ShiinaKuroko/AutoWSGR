"""系统基础能力命名空间。

能力范围：通用枚举、错误基类、文件边界和日志基础设施。
下层依赖：Python 标准库及已批准的第三方库。
边界：不持有业务配置、页面状态、设备对象或具体领域错误。
"""

from autowsgr.common.system import enums, errors, files, logger


__all__ = ['enums', 'errors', 'files', 'logger']
