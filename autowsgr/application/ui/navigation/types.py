"""模块功能：定义导航器的页面契约与错误。

上层调用：
- application.ui.navigation.service 与 registry：使用页面契约与错误。
- 各 UI 控制器：用 PageName 表达目标页面。

下层依赖：
- common.system.enums：提供字符串枚举基类。
- common.system.errors：提供应用错误基类。

边界：只定义数据契约与错误类型，不含导航逻辑、识别或点击。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from autowsgr.common.system.enums import StrEnum
from autowsgr.common.system.errors import ApplicationError


if TYPE_CHECKING:
    from collections.abc import Callable


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


@dataclass(frozen=True, slots=True)
class NavTarget:
    """从某个页面可以直达的一个目标。

    Attributes:
        target: 目标页面。
        action: 执行一次点击的动作，可接收调用方透传的参数。
        description: 这条边的说明，供维护与日志使用。
    """

    target: PageName
    action: Callable[..., None]
    description: str = ''


class NavigationError(ApplicationError):
    """导航失败时抛出。"""


__all__ = ['NavTarget', 'NavigationError', 'PageName']
