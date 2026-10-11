"""模块功能：定义导航器的页面名与导航错误。

上层调用：
- application.ui.navigation 与各 UI 控制器：用 PageName 表达目标页面。
- dispatch.startup：捕获 ManualUpdateRequiredError 转成人工处理错误。

下层依赖：
- common.system.enums：提供字符串枚举基类。
- common.system.errors：提供应用错误基类。

边界：只定义页面名与错误类型，不含导航逻辑、识别或点击；
它必须保持零依赖，供所有层级（含下层控制器）导入。
"""

from __future__ import annotations

from autowsgr.common.system.enums import StrEnum
from autowsgr.common.system.errors import ApplicationError


class PageName(StrEnum):
    """游戏页面名称。"""

    LOGIN_PAGE = '登录页面'
    SERVER_SELECT = '区服选择页面'
    HOME = '主页面'
    SORTIE_MAP = '出征页面'
    EXERCISE = '演习页面'
    EXPEDITION = '远征页面'
    CAMPAIGN = '战役页面'
    BATTLE_PREP = '出征准备'
    SIDEBAR = '侧边栏'
    MISSION = '任务页面'
    BACKYARD = '后院页面'
    BATH = '浴室页面'
    CANTEEN = '食堂页面'
    CHOOSE_REPAIR = '选择修理页面'
    BUILD = '建造页面'
    INTENSIFY = '强化页面'
    FRIEND = '好友页面'
    DECISIVE_BATTLE = '决战页面'
    CHOOSE_SHIP = '选择舰船页面'
    EVENT_MAP = '活动页面'
    EVENT_STAGE_OVERLAY = '活动章节浮窗'


class NavigationError(ApplicationError):
    """导航失败时抛出。"""


class ManualUpdateRequiredError(NavigationError):
    """游戏需要更新，导航无法继续。

    这不是导航失败：重启游戏也不会改变，应由处理器转成需要人工介入的错误。
    """


__all__ = ['ManualUpdateRequiredError', 'NavigationError', 'PageName']
