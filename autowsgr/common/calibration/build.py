"""Build page calibration used by the build Controller.

All points are loaded from ``common/data/calibration/coordinates/build.yaml``;
tab meaning and build workflow stay in the Controller.
"""

from autowsgr.common.calibration.coordinates import point, points


CLICK_BACK = point('build', 'back')
TAB_POSITIONS = {
    name: point('build', f'tabs.{name}') for name in ('build', 'destroy', 'develop', 'discard')
}
SLOT_POSITIONS = points('build', 'slots')
CLICK_CONFIRM = point('build', 'confirm')
CLICK_DESTROY_ADD = point('build', 'destroy.add')
CLICK_DESTROY_QUICK_SELECT = point('build', 'destroy.quick_select')
CLICK_DESTROY_CONFIRM_SELECT = point('build', 'destroy.confirm_select')
CLICK_DESTROY_REMOVE_EQUIP = point('build', 'destroy.remove_equip')
CLICK_DESTROY_CONFIRM = point('build', 'destroy.confirm')
CLICK_DESTROY_FOUR_STAR_CONFIRM = point('build', 'destroy.four_star_confirm')
CLICK_DESTROY_TYPE_FILTER = point('build', 'destroy.type_filter')
CLICK_DESTROY_CONFIRM_FILTER = point('build', 'destroy.confirm_filter')
CLICK_DISMISS_ANIMATION = point('build', 'dismiss_animation')


__all__ = [
    'CLICK_BACK',
    'CLICK_CONFIRM',
    'CLICK_DESTROY_ADD',
    'CLICK_DESTROY_CONFIRM',
    'CLICK_DESTROY_CONFIRM_FILTER',
    'CLICK_DESTROY_CONFIRM_SELECT',
    'CLICK_DESTROY_FOUR_STAR_CONFIRM',
    'CLICK_DESTROY_QUICK_SELECT',
    'CLICK_DESTROY_REMOVE_EQUIP',
    'CLICK_DESTROY_TYPE_FILTER',
    'CLICK_DISMISS_ANIMATION',
    'SLOT_POSITIONS',
    'TAB_POSITIONS',
]
