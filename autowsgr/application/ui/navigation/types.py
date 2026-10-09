"""UI 导航领域类型。"""

from __future__ import annotations

from dataclasses import dataclass

from autowsgr.common.system.enums import StrEnum


class PageName(StrEnum):
    """游戏页面名称。"""

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

