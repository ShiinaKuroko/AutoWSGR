"""地图页面子包。

re-export 公开 API，外部统一通过 ``autowsgr.infra.base.ui.pages.map`` 导入。
"""

from autowsgr.infra.base.ui.pages.map.base import BaseMapPage
from autowsgr.infra.base.ui.pages.map.data import MapIdentity, MapPanel, parse_map_title
from autowsgr.infra.base.ui.pages.map.page import MapPage

__all__ = [
    'BaseMapPage',
    'MapIdentity',
    'MapPage',
    'MapPanel',
    'parse_map_title',
]
