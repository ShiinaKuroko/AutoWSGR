"""主页面常量 — 枚举类封装。

数据源 (infra/base/constants 分类管理):
    - 导航/探测/浮层消除坐标: coordinates/main.yaml (1280x720 绝对像素,
      经 point() 归一化为相对值)
    - 颜色: colors/main.yaml
    - 像素签名: signatures/main.yaml
本模块只保留访问器枚举, 值全部来自 YAML 单源。
"""

from __future__ import annotations

import enum

from autowsgr.infra.base.constants.colors import color as _color
from autowsgr.infra.base.constants.colors import tolerance as _color_tolerance
from autowsgr.infra.base.constants.coordinates import point
from autowsgr.infra.base.constants.signatures import signature
from autowsgr.types import PageName
from autowsgr.vision import Color, PixelSignature


# ═══════════════════════════════════════════════════════════════════════════════
# 导航目标
# ═══════════════════════════════════════════════════════════════════════════════


class Target(enum.Enum):
    """主页面可导航的目标。"""

    SORTIE = '出征'
    TASK = '任务'
    SIDEBAR = '侧边栏'
    HOME = '主页'
    EVENT = '活动'

    @property
    def page_name(self) -> str:
        """对应的目标页面名称。"""
        return _TARGET_PAGES[self]


_TARGET_PAGES: dict[Target, str] = {
    Target.SORTIE: PageName.MAP,
    Target.TASK: PageName.MISSION,
    Target.SIDEBAR: PageName.SIDEBAR,
    Target.HOME: PageName.BACKYARD,
    Target.EVENT: PageName.EVENT_MAP,
}


# ═══════════════════════════════════════════════════════════════════════════════
# 浮层类型
# ═══════════════════════════════════════════════════════════════════════════════


class OverlayKind(enum.Enum):
    """主页面可出现的浮层类型。"""

    NEWS = '新闻公告'
    SIGN = '每日签到'
    BOOKING = '活动预约'
    USER_INFO = '提督信息'


# ═══════════════════════════════════════════════════════════════════════════════
# 坐标枚举
# ═══════════════════════════════════════════════════════════════════════════════


class NavCoord(enum.Enum):
    """导航目标点击坐标 — 数据源: coordinates/main.yaml。

    枚举值为 YAML 键名 (支持点号嵌套路径, 如 ``backyard.enter``),
    ``.xy`` 实时读取归一化坐标。
    """

    SORTIE = 'sortie'
    TASK = 'task'
    SIDEBAR = 'menu.enter'
    HOME = 'backyard.enter'
    EVENT = 'event'

    @property
    def xy(self) -> tuple[float, float]:
        """归一化坐标 (YAML 键名 → point() 查询)。"""
        return point('main', self.value)


class ProbePoint(enum.Enum):
    """状态探测点坐标 — 数据源: coordinates/main.yaml (probes.*)。"""

    EXPEDITION_READY = 'probes.expedition_ready'
    """远征完成探测点。"""

    TASK_READY = 'probes.task_ready'
    """任务可领取探测点。"""

    @property
    def xy(self) -> tuple[float, float]:
        return point('main', self.value)


class DismissCoord(enum.Enum):
    """浮层 / 弹窗消除点击坐标 — 数据源: coordinates/main.yaml (dismiss.*)。"""

    NEWS_NOT_SHOW = 'dismiss.news_not_show'
    """新闻「不再显示」复选框 — 5.6.0 版式。"""

    NEWS_CLOSE = 'dismiss.news_close'
    """新闻关闭按钮 — 5.6.0 版式。"""

    SIGN_CONFIRM = 'dismiss.sign_confirm'
    """签到领取/关闭按钮。"""

    BOOKING = 'dismiss.booking'
    """预约页面关闭坐标。"""

    USER_INFO_CLOSE = 'dismiss.user_info_close'
    """提督信息浮层关闭按钮 (右上角 X)。"""

    @property
    def xy(self) -> tuple[float, float]:
        return point('main', self.value)


# ═══════════════════════════════════════════════════════════════════════════════
# 颜色 & 容差
# ═══════════════════════════════════════════════════════════════════════════════


class ThemeColor(enum.Enum):
    """主页面关键颜色 — 数据源: colors/main.yaml。"""

    NOTIFICATION_RED = 'notification_red'
    """通知红点。"""

    EVENT_SIDEBAR_BG = 'event_sidebar_bg'
    """侧边栏无活动时背景灰色。"""

    @property
    def color(self) -> Color:
        return _color('main', self.value)

    @property
    def tolerance(self) -> float:
        return _color_tolerance('main', self.value)


# ═══════════════════════════════════════════════════════════════════════════════
# 像素签名
# ═══════════════════════════════════════════════════════════════════════════════


class Sig(enum.Enum):
    """主页面像素签名 — 数据源: signatures/main.yaml。

    通过 ``.ps`` 属性访问 :class:`PixelSignature` 实例。
    """

    PAGE = 'page'
    """主页面基础签名 — 检测资源栏 + 角落特征。"""

    NEWS = 'news'
    """新闻公告浮层签名。"""

    NEWS_NOT_SHOW = 'news_not_show'
    """「不再显示」复选框已勾选态签名 (蓝色)。"""

    SIGN = 'sign'
    """每日签到浮层签名。"""

    BOOKING = 'booking'
    """预约页面签名。"""

    @property
    def ps(self) -> PixelSignature:
        """对应的 :class:`PixelSignature` 实例。"""
        return signature('main', self.value)
