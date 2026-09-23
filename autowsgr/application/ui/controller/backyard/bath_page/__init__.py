"""模块功能：导出浴室页面控制器和修理卡片结果契约。

上层调用：
- application.ui.navigation：注册浴室页面检查器并执行页面导航。
- business.logistics.repair：调用浴室修理页面入口。

下层依赖：
- application.ui.controller.backyard.bath_page.page：提供页面流程和导航控制器。
- application.ui.controller.backyard.bath_page.recognition：提供页面事实实现。

边界：
本包只提供稳定导出，不执行页面注册、设备操作或 OCR 初始化。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.backyard.bath_page.page import (
    BathPage,
    RepairResult,
)


__all__ = ['BathPage', 'RepairResult']
