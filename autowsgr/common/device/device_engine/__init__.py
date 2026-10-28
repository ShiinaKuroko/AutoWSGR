"""模块功能：设备引擎包命名空间。

上层调用：
- common.device.service 和 common.device.device_engine 内部流程：按子包路径导入设备能力。

下层依赖：
- 本包的 foundation、orchestration 和 session 子模块。

只做包命名空间，不导出具体能力。
"""

__all__: list[str] = []
