"""模块功能：定义 UI Controller 运行时依赖的结构协议。

直接调用方：UI Controller 页面、导航旧实现和 UI 流程测试。

直接依赖：Python 类型协议和运行时注入对象。

边界：只描述 UI Controller 所需的注入依赖，不持有跨步骤状态或创建运行时对象。
"""

from __future__ import annotations

from typing import Any, Protocol


class UIContext(Protocol):
    """描述 UI Controller 可读取的运行时依赖。"""

    ctrl: Any
    config: Any
    ocr: Any
    ship_ocr: Any
    ui_stack: Any
    current_page: Any
    daily_overlay_checked: bool
    latest_screenshot: Any

    def record_screenshot(self, screen: Any) -> None:
        """保存识别链路最近一次截图。"""


__all__ = ['UIContext']
