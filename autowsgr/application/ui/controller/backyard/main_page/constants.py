"""维护后院页面共享的导航坐标。

上层调用：
- application.ui.controller.backyard.main_page.page：读取页面导航坐标。

下层依赖：
- 无。

边界：
只保存后院页面静态坐标，不保存页面状态、设备对象或导航规则。
"""

from __future__ import annotations


# 坐标按 1280x720 设计分辨率校准，并以相对坐标保存。
CLICK_BACK = (0.0219, 0.0583)  # 后院页面左上角返回按钮，用于回到主页面。
CLICK_BATH = (0.3125, 0.3708)  # 后院浴室入口，用于进入浴室页面。
CLICK_CANTEEN = (0.7289, 0.7403)  # 后院食堂入口，用于进入食堂页面。


__all__ = ['CLICK_BACK', 'CLICK_BATH', 'CLICK_CANTEEN']
