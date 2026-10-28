"""模块功能：ADB 执行器包出口。

上层调用：
- common.device.device_engine.orchestration.connection、discovery 和 lifecycle：取用 ADB 执行器。

下层依赖：
- common.device.adb_engine.executor：提供主机侧 ADB 能力。

只导出执行器模块，不实现 ADB 逻辑。
"""

from autowsgr.common.device.adb_engine import executor


__all__ = ['executor']
