"""决战领域状态类型。"""

from __future__ import annotations

import enum

from autowsgr.common.system.enums import StrEnum


class DecisiveEntryStatus(StrEnum):
    """决战总览页入口状态。"""

    CANT_FIGHT = 'cant_fight'
    CHALLENGING = 'challenging'
    REFRESHED = 'refreshed'
    REFRESH = 'refresh'


class DecisivePhase(enum.Enum):
    """决战过程的宏观阶段。"""

    INIT = enum.auto()
    ENTER_MAP = enum.auto()
    WAITING_FOR_MAP = enum.auto()
    USE_LAST_FLEET = enum.auto()
    CHOOSE_FLEET = enum.auto()
    ADVANCE_CHOICE = enum.auto()
    PREPARE_COMBAT = enum.auto()
    IN_COMBAT = enum.auto()
    NODE_RESULT = enum.auto()
    STAGE_CLEAR = enum.auto()
    CHAPTER_CLEAR = enum.auto()
    RETREAT = enum.auto()
    LEAVE = enum.auto()
    DOCK_FULL = enum.auto()
    FINISHED = enum.auto()
