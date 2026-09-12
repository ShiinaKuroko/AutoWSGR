"""模块功能：维护母港主页专用的坐标、颜色和像素签名。

上层调用：
- application.ui.controller.home.main_page.page：执行母港导航和通知状态检查。
- application.ui.controller.home.main_page.overlay：执行母港浮层消除。
- application.ui.navigation.event：点击活动入口。

下层依赖：
- common.vision：提供颜色和像素签名的数据类型。

本模块不保存页面状态、设备对象、运行时上下文或导航业务规则。
兼容校准 YAML 仍由通用校准测试保留；主页控制器使用这里的页面私有值。
"""

from autowsgr.common.vision import Color, PixelRule, PixelSignature


# ── 页面导航坐标 ─────────────────────────────────────────────────────────────

NAV_POSITIONS = {
    'sortie': (0.9430, 0.9069),  # 母港出征入口，用于进入地图选择页面。
    'task': (0.6836, 0.9042),  # 母港任务入口，用于进入任务页面。
    'sidebar': (0.0516, 0.8972),  # 母港侧边栏入口，用于打开侧边栏菜单。
    'home': (0.0484, 0.1556),  # 母港后院入口，用于进入后院页面。
    'event': (0.8844, 0.4833),  # 母港活动入口，用于进入活动地图页面。
}

# ── 母港通知探测坐标 ─────────────────────────────────────────────────────────

PROBE_POSITIONS = {
    'expedition_ready': (0.9719, 0.8403),  # 远征完成红点，用于判断是否有远征奖励可收取。
    'task_ready': (0.7227, 0.8458),  # 任务按钮红点，用于判断是否有任务奖励可领取。
}

# ── 浮层消除坐标 ─────────────────────────────────────────────────────────────

DISMISS_POSITIONS = {
    'news_not_show': (0.0664, 0.9000),  # 新闻「不再显示」复选框，用于关闭后续新闻提示。
    'news_close': (0.0352, 0.0625),  # 新闻公告关闭按钮，用于离开新闻浮层。
    'sign_confirm': (0.4938, 0.6611),  # 每日签到领取/确认按钮，用于提交签到奖励。
    'booking': (0.6180, 0.5639),  # 活动预约关闭按钮，用于返回母港页面。
    'user_info_close': (0.8773, 0.2208),  # 提督信息浮层关闭按钮，用于返回母港页面。
}

# ── 母港通知颜色 ─────────────────────────────────────────────────────────────

NOTIFICATION_RED = Color.of(255, 89, 45)  # 远征和任务通知红点的目标颜色。
NOTIFICATION_RED_TOLERANCE = 40.0  # 通知红点颜色比较容差，用于覆盖渲染差异。

# ── 母港页面像素签名 ─────────────────────────────────────────────────────────

PAGE_SIGNATURE = PixelSignature(
    name='主页面',
    rules=(
        PixelRule.of(0.6453, 0.9375, (52, 115, 168), tolerance=30.0),  # 底部资源栏蓝色锚点。
        PixelRule.of(0.8126, 0.8681, (213, 206, 180), tolerance=30.0),  # 右下区域米色锚点。
        PixelRule.of(0.9696, 0.8903, (121, 130, 135), tolerance=30.0),  # 右侧背景灰色锚点。
        PixelRule.of(0.0570, 0.8847, (251, 252, 255), tolerance=30.0),  # 左下区域浅色锚点。
    ),
)  # 母港基础页面像素签名，用于模板匹配失败时的识别兜底。

NEWS_NOT_SHOW_SIGNATURE = PixelSignature(
    name='news_not_show',
    rules=(
        PixelRule.of(0.0672, 0.9014, (54, 129, 201), tolerance=40.0),  # 复选框左侧蓝色像素。
        PixelRule.of(0.0696, 0.9014, (54, 129, 201), tolerance=40.0),  # 复选框右侧蓝色像素。
    ),
)  # 新闻复选框已勾选签名，用于避免重复点击。


__all__ = [
    'DISMISS_POSITIONS',
    'NAV_POSITIONS',
    'NEWS_NOT_SHOW_SIGNATURE',
    'NOTIFICATION_RED',
    'NOTIFICATION_RED_TOLERANCE',
    'PAGE_SIGNATURE',
    'PROBE_POSITIONS',
]
