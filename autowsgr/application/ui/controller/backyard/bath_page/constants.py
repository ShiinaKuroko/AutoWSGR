"""模块功能：维护浴室页面跨文件共享的坐标和颜色校准参数。

上层调用：
- application.ui.controller.backyard.bath_page.page：读取页面级导航和操作坐标。
- application.ui.controller.backyard.bath_page.operations：读取设备操作坐标和滑动参数。
- application.ui.controller.backyard.bath_page.recognition：读取页面、按钮和卡片识别校准。

下层依赖：
- 无。

边界：
本模块只保存浴室页面静态校准数据，不保存上下文、设备对象、流程状态或业务调度。
"""

from __future__ import annotations


# ── 页面导航和浮层坐标（归一化相对坐标） ────────────────────────────────────────

CLICK_BACK = (0.0219, 0.0583)  # 浴室页面左上角返回按钮。
CLICK_CHOOSE_REPAIR = (0.9375, 0.0556)  # 浴室页面的选择修理入口。
CLICK_CLOSE_OVERLAY = (0.9563, 0.0903)  # 选择修理浮层的关闭按钮。

# ── 修理卡片操作坐标（归一化相对坐标） ─────────────────────────────────────────

CLICK_REPAIR_ALL = (0.6805, 0.1708)  # 选择修理浮层的全部修理按钮。
CLICK_FIRST_REPAIR_SHIP = (0.1195, 0.4319)  # 修理列表第一张舰船卡片。

# ── 修理列表滑动坐标（归一化相对坐标） ─────────────────────────────────────────

SWIPE_START = (0.6602, 0.5000)  # 从修理列表右侧开始滑动。
SWIPE_END = (0.3297, 0.5000)  # 向左滑到修理列表左侧。

# ── 浮层按钮颜色 ─────────────────────────────────────────────────────────────

REPAIR_ALL_BUTTON_COLOR = ((17, 119, 216), 30.0)  # (RGB, 容差): 全部修理按钮。
CLOSE_OVERLAY_BUTTON_COLOR = ((197, 199, 194), 30.0)  # (RGB, 容差): 浮层关闭按钮。
