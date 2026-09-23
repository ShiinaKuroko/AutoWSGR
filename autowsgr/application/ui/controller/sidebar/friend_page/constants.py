"""模块功能：维护好友页面专用的返回坐标。

上层调用：
- application.ui.controller.sidebar.friend_page.page：执行好友页面返回侧边栏。

下层依赖：
- 无。坐标来自好友页面 1280x720 校准结果，并以归一化相对值保存。

边界：
只保存好友页面静态坐标，不保存页面状态、设备对象、运行时上下文或好友业务规则。
"""

from __future__ import annotations


# 坐标按 1280x720 设计分辨率校准，并以归一化相对值保存。
CLICK_BACK = (0.0219, 0.0583)  # 好友页面左上角返回按钮，用于回到侧边栏。


__all__ = ['CLICK_BACK']
