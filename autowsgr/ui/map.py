"""兼容 shim — 实现已迁移至 :mod:`autowsgr.infra.base.ui.pages.map`。

老代码仍可 ``from autowsgr.ui.map import MapPage ...`` 或
``from autowsgr.ui.map.data import X ...``，新代码请直接使用新路径。
"""

from autowsgr.infra.base.ui.pages.map import (
    BaseMapPage,
    MapPage,
    MapIdentity,
    MapPanel,
    parse_map_title,
)
from autowsgr.infra.base.ui.pages.map import data as _data
from autowsgr.infra.base.ui.pages.map.data import (  # noqa: F401
    CAMPAIGN_POSITIONS,
    CHAPTER_MAP_COUNTS,
    CLICK_BACK,
    CLICK_DIFFICULTY,
    CLICK_ENTER_DECISIVE,
    CLICK_ENTER_SORTIE,
    CLICK_MAP_NEXT,
    CLICK_MAP_PREV,
    CLICK_PANEL,
    DIFFICULTY_EASY_COLOR,
    DIFFICULTY_HARD_COLOR,
    EXERCISE_ARROW_DOWN_PROBE,
    EXERCISE_ARROW_GRAY,
    EXERCISE_ARROW_TOLERANCE,
    EXERCISE_ARROW_UP_PROBE,
    EXERCISE_CHALLENGE_COLOR,
    EXERCISE_CHALLENGE_PROBES,
    EXERCISE_CHALLENGE_TOLERANCE,
    EXERCISE_CLICK_RIVAL_INFO,
    EXERCISE_CLICK_START_BATTLE,
    EXERCISE_SWIPE_DELAY,
    EXERCISE_SWIPE_TO_BOTTOM,
    EXERCISE_SWIPE_TO_TOP,
    EXPEDITION_IDLE_COLOR,
    EXPEDITION_NOTIF_COLOR,
    EXPEDITION_NOTIF_PROBE,
    EXPEDITION_READY_COLOR,
    EXPEDITION_SLOT_PROBES,
    EXPEDITION_SLOT_TOLERANCE,
    EXPEDITION_TOLERANCE,
    MAP_DATABASE,
    MAP_NODE_POSITIONS,
    PANEL_LIST,
    PANEL_TO_INDEX,
    RIVAL_POSITIONS,
    TITLE_CROP_REGION,
    TOTAL_CHAPTERS,
)

# 老用法 ``from autowsgr.ui.map.data import X`` 仍可用 (模块属性透传)
data = _data
