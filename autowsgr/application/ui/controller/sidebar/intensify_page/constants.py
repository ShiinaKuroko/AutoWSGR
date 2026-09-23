"""模块功能：维护强化页面返回导航的校准坐标。

上层调用：
- application.ui.controller.sidebar.intensify_page.page：执行返回侧边栏。

下层依赖：
- 无。坐标来自强化页面 1280x720 校准结果，并以归一化相对值保存。

边界：
本模块不保存页面状态、设备对象、运行时上下文或强化业务规则。
"""

from __future__ import annotations


CLICK_BACK = (0.0219, 0.0583)  # 强化页面左上角返回按钮，用于回到侧边栏。

__all__ = ['CLICK_BACK']
