"""Sidebar calibration used by the sidebar Controller."""

from autowsgr.common.calibration.coordinates import point


CLICK_CLOSE = point('sidebar', 'close')
NAV_POSITIONS = {
    name: point('sidebar', f'nav.{name}') for name in ('build', 'intensify', 'friend')
}
SUBMENU_POSITIONS = {
    name: point('sidebar', f'submenu.{name}') for name in ('build', 'intensify')
}


__all__ = ['CLICK_CLOSE', 'NAV_POSITIONS', 'SUBMENU_POSITIONS']
