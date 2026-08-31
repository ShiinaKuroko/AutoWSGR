"""地图页面的物理坐标。"""

from __future__ import annotations

from autowsgr.common.calibration.coordinates import point


CLICK_BACK = point('map', 'back')
PANEL_POSITIONS = {
    name: point('map', f'panel.{name}')
    for name in ('sortie', 'exercise', 'expedition', 'battle', 'decisive')
}


__all__ = ['CLICK_BACK', 'PANEL_POSITIONS']
