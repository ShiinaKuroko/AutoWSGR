"""地图页面子包。

re-export 公开 API，外部统一通过 ``autowsgr.application.ui.controller.map`` 导入。
"""

from autowsgr.application.ui.controller.map.base import BaseMapPage
from autowsgr.application.ui.controller.map.data import MapIdentity, MapPanel, parse_map_title
from autowsgr.application.ui.controller.map.page import MapPage


__all__ = [
    'BaseMapPage',
    'MapIdentity',
    'MapPage',
    'MapPanel',
    'parse_map_title',
]
