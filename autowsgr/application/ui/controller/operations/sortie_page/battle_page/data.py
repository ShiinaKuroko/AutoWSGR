"""模块功能：保存地图面板枚举和章节地图数据。

上层调用：
- application.ui.controller.operations.sortie_page.battle_page.base：读取面板顺序和章节数量。
- application.ui.controller.operations.sortie_page：驱动顶部标签面板业务。
- testing.ui：验证地图标题数据和面板结构。

下层依赖：
- application.ui.controller.operations.sortie_page.battle_page.constants：提供固定章节槽位锚点索引。

本模块只保存页面业务所需的数据和值类型，不读取截图、不调用 OCR，也不操作设备。
地图标题的 OCR 结果模型和文本解析由 recognition.py 负责。
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from autowsgr.application.ui.controller.operations.sortie_page.battle_page.constants import (
    CHAPTER_SLOT_CENTER_INDEX,
)


# ── 章节地图数据 ────────────────────────────────────────────────────────────

MAP_DATABASE: dict[tuple[int, int], str] = {
    # 第一章：母港周边哨戒
    (1, 1): '母港附近海域',
    (1, 2): '东北防线海域',
    (1, 3): '仁州附近海域',
    (1, 4): '深海仁州基地',
    (1, 5): '乌兰巴托附近水域',
    # 第二章：扶桑海域攻略
    (2, 1): '扶桑西部海域',
    (2, 2): '扶桑西南海域',
    (2, 3): '扶桑南部海域',
    (2, 4): '深海扶桑基地',
    (2, 5): '深海前哨核心地区',
    (2, 6): '深海前哨北方地区',
    # 第三章：星洲海峡突破
    (3, 1): '母港南部海域',
    (3, 2): '东南群岛（1）',
    (3, 3): '东南群岛（2）',
    (3, 4): '星洲海峡',
    # 第四章：西行航线开辟
    (4, 1): '克拉代夫东部海域',
    (4, 2): '克拉代夫西部海域',
    (4, 3): '泪之扉附近海域',
    (4, 4): '泪之扉防线',
    # 第五章：地中海死斗
    (5, 1): '塞浦路斯附近海域',
    (5, 2): '克里特附近海域',
    (5, 3): '马耳他附近海域',
    (5, 4): '直布罗陀东部海域',
    (5, 5): '直布罗陀要塞',
    # 第六章：北海风暴
    (6, 1): '洛里昂南部海域',
    (6, 2): '英吉利海峡',
    (6, 3): '斯卡帕湾',
    (6, 4): '丹麦海峡',
    # 第七章：比斯开湾战役
    (7, 1): '比斯开湾',
    (7, 2): '马德拉海域',
    (7, 3): '亚速尔海域',
    (7, 4): '百慕大三角附近海域',
    (7, 5): '百慕大三角防波堤',
    # 第八章：新大陆海域鏖战
    (8, 1): '百慕大中心海域',
    (8, 2): '百慕大南群岛',
    (8, 3): '北加勒比海域',
    (8, 4): '东部海岸群岛',
    (8, 5): '地峡海湾',
    # 第九章：南狭长海域
    (9, 1): '地峡外海',
    (9, 2): '大洋南湾',
    (9, 3): '南入海口海域',
    (9, 4): '河口外海',
    (9, 5): '南大洋群岛',
    # 第十章：极地水域
    (10, 1): '极地海峡',
}
"""已知地图的章节和关卡号到地图名称映射。"""

CHAPTER_MAP_COUNTS: dict[int, int] = {}
"""每章地图数量，用于限制普通出征的章节导航范围。"""

for _chapter, _map_num in MAP_DATABASE:
    CHAPTER_MAP_COUNTS[_chapter] = max(
        CHAPTER_MAP_COUNTS.get(_chapter, 0),
        _map_num,
    )

TOTAL_CHAPTERS: int = 10
"""当前普通出征地图的总章节数，用于校验章节参数。"""


# ── 顶部标签状态 ────────────────────────────────────────────────────────────


class MapPanel(enum.Enum):
    """地图页面顶部导航面板。"""

    SORTIE = '出征'
    EXERCISE = '演习'
    EXPEDITION = '远征'
    BATTLE = '战役'
    DECISIVE = '决战'


PANEL_LIST: list[MapPanel] = list(MapPanel)
"""顶部标签顺序，用于把识别到的标签索引映射为面板。"""

PANEL_TO_INDEX: dict[MapPanel, int] = {panel: index for index, panel in enumerate(PANEL_LIST)}
"""面板到顶部标签索引的映射，用于切换面板和构造到达检查器。"""


@dataclass(frozen=True, slots=True)
class ChapterSlot:
    """一个固定章节槽位的 OCR 结果和页面索引。"""

    index: int
    chapter: int | None
    text: str
    confidence: float


def choose_chapter_slot(
    current: int,
    target: int,
    slots: tuple[ChapterSlot, ...],
) -> int | None:
    """选择一个已识别且能证明方向的章节槽位。"""
    for slot in slots:
        if slot.chapter == target:
            return slot.index

    delta = target - current
    if delta == 0:
        return None

    step = 2 if abs(delta) >= 2 else 1
    direction = 1 if delta > 0 else -1
    index = CHAPTER_SLOT_CENTER_INDEX + direction * step
    if not 0 <= index < len(slots):
        return None

    expected = current + direction * step
    return index if slots[index].chapter == expected else None


__all__ = [
    'CHAPTER_MAP_COUNTS',
    'MAP_DATABASE',
    'PANEL_LIST',
    'PANEL_TO_INDEX',
    'TOTAL_CHAPTERS',
    'ChapterSlot',
    'MapPanel',
    'choose_chapter_slot',
]
