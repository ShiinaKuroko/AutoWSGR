"""模块功能：定义设备基础能力的错误类型。

上层调用：
- common.device 内各执行器、设备流程和设备能力使用方：抛出或捕获设备错误。

下层依赖：
- common.system.errors：提供公共错误基类。

边界：只定义错误类型，不负责记录日志或恢复设备状态。
"""

from __future__ import annotations

from autowsgr.common.system.errors import CommonError


class DeviceError(CommonError):
    """设备操作失败。"""


class DeviceConnectionError(DeviceError):
    """设备连接或通信失败。"""


class DeviceNotFoundError(DeviceError):
    """未找到设备或设备所需的宿主资源。"""


class GameError(DeviceError):
    """设备运行期间的游戏通道错误。"""


class NetworkError(GameError):
    """游戏网络错误。"""


class ResourceError(GameError):
    """游戏资源不足或资源状态错误。"""


__all__ = [
    'DeviceConnectionError',
    'DeviceError',
    'DeviceNotFoundError',
    'GameError',
    'NetworkError',
    'ResourceError',
]
