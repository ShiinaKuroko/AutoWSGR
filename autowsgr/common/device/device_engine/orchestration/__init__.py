"""模块功能：设备引擎流程包命名空间。

上层调用：
- common.device.service 和 common.device.device_engine.session：按子模块路径导入设备流程。

下层依赖：
- 本包的 connection、discovery、operation、screenshot 和 lifecycle。

边界：只做包命名空间，不导出具体能力。
"""

__all__: list[str] = []
