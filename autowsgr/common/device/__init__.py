"""模块功能：提供设备基础能力的统一命名空间。

上层调用：
- application、business、dispatch 和 server：通过 common.device.service 取用设备连接、输入和截图。

下层依赖：
- common.device.service、common.device.config 和 common.system 基础能力。

边界：不识别游戏页面、不编排业务流程、不持有任务或用户业务状态。
"""

from __future__ import annotations

from autowsgr.common.device import service


__all__ = [
    'service',
]
