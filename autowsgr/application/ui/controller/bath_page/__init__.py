"""模块功能：导出浴室页面 Controller 和修理卡片识别契约。

上层调用：
- application.ui.navigation.registry：注册浴室页面识别器。
- business.logistics.repair.bath_repair：取得浴室页面操作入口。

下层依赖：
- application.ui.controller.bath_page.page：提供页面识别、浮层操作和页面返回。
- application.ui.controller.bath_page.recognition：提供卡片数据模型、识别和时长转换。

本模块只负责公开导出，不执行页面注册或其他导入副作用。
"""

from .page import BathPage
from .recognition import RepairShipInfo, convert_repair_time_to_seconds, recognize_repair_cards


__all__ = [
    'BathPage',
    'RepairShipInfo',
    'convert_repair_time_to_seconds',
    'recognize_repair_cards',
]
