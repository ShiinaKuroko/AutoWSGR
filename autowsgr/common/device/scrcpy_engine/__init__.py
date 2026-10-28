"""模块功能：Scrcpy 执行器包出口。

上层调用：
- common.device.device_engine.session：取用 Scrcpy 执行器。

下层依赖：
- common.device.scrcpy_engine.executor：提供 Scrcpy 通道和输入能力。

只导出执行器模块，不实现 Scrcpy 逻辑。
"""

from autowsgr.common.device.scrcpy_engine import executor


__all__ = ['executor']
