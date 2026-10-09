"""模块功能：维护活动页面在各玩法之间通用的点击坐标。

上层调用：
- application.ui.controller.home.event_page.page：读取通用落点。

下层依赖：无，只保存静态坐标。

边界：只保存点击坐标，不识别画面、不编排流程、不持有运行状态。
"""

from __future__ import annotations


# 左上角返回按钮的落点，点击后从活动地图回到首页。
CLICK_HOME_BACK = (0.0329, 0.0570)
# 章节浮窗右上角关闭按钮的落点，点击后从浮窗回到活动地图。
CLICK_OVERLAY_CLOSE = (0.9532, 0.1048)
