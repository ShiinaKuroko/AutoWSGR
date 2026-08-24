"""任务页面子包 — 页面识别 / 状态查询 / 操作动作。

UI 基础实现的归属地 (与 main_page / map 同级), 旧路径
``autowsgr.ui.mission_page`` 为兼容 shim。
"""

from autowsgr.infra.base.ui.pages.mission_page.data import (
    ButtonType,
    MissionInfo,
    MissionPanel,
)
from autowsgr.infra.base.ui.pages.mission_page.page import MissionPage

__all__ = [
    'ButtonType',
    'MissionInfo',
    'MissionPage',
    'MissionPanel',
]
