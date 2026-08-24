"""兼容 shim — 实现已迁移至 :mod:`autowsgr.infra.base.ui.pages.mission_page`。

老代码仍可 ``from autowsgr.ui.mission_page import MissionPage``，
新代码请直接使用新路径。
"""

from autowsgr.infra.base.ui.pages.mission_page import (
    ButtonType,
    MissionInfo,
    MissionPage,
    MissionPanel,
)

__all__ = [
    'ButtonType',
    'MissionInfo',
    'MissionPage',
    'MissionPanel',
]
