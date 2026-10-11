"""模块功能：系统基础能力命名空间。

上层调用：
- application、business、dispatch 和 server：通过 system.enums、system.errors、
  system.files、system.logger 取用通用基础能力。
- common.device 和 common.vision：使用系统错误基类和日志基础设施。

下层依赖：
- enums、errors、files 和 logger 四个子模块。

边界：只做能力命名空间，不持有业务配置、页面状态、设备对象或具体领域错误。
"""

from autowsgr.common.system import enums, errors, files, logger


__all__ = ['enums', 'errors', 'files', 'logger']
