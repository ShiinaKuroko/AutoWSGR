"""模块功能：设备引擎基础能力包出口。

上层调用：
- common.device.config 和 common.device.device_engine.orchestration：取用平台事实与操作延迟。

下层依赖：
- common.device.device_engine.foundation.delay 和 platform。

只导出基础能力模块，不实现平台逻辑。
"""

from autowsgr.common.device.device_engine.foundation import delay, platform


__all__ = ['delay', 'platform']
