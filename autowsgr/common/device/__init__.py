"""提供设备基础能力的统一命名空间。

直接调用方：需要使用设备基础能力的应用、业务和工具模块。
下层依赖：device.service、device.config 和 system 基础能力。
边界：不识别游戏页面、不编排业务流程、不持有任务或用户业务状态。
"""

from __future__ import annotations

from autowsgr.common.device import service


__all__ = [
    'service',
]
