"""Check the shared map-counter boundary and the sortie page contract."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    """Validate common counter ownership and sortie entry points."""
    errors: list[str] = []
    try:
        from autowsgr.application.ui.controller.operations.sortie_page.battle_page import (
            BattlePage,
            recognition,
        )
        from autowsgr.common.vision import map
        from autowsgr.common.vision.map import (
            LOOT_MAX,
            SHIP_MAX,
            LootShipCount,
            recognize_loot_count,
            recognize_ship_count,
        )
    except Exception as exc:
        errors.append(f'canonical imports failed: {exc}')
    else:
        old_module = (
            PROJECT_ROOT
            / 'autowsgr/application/ui/controller/operations/sortie_page/battle_page/panels/sortie_counters.py'
        )
        if old_module.exists():
            errors.append('old Controller counter module still exists')
        if (LOOT_MAX, SHIP_MAX) != (50, 500):
            errors.append(f'counter limits are {(LOOT_MAX, SHIP_MAX)}, expected (50, 500)')
        fields = tuple(LootShipCount.__dataclass_fields__)
        if fields != ('loot', 'loot_max', 'ship', 'ship_max'):
            errors.append(f'LootShipCount fields are {fields}')
        if map.LootShipCount is not LootShipCount:
            errors.append('common counter module exposes a duplicate model')
        for name, expected in (
            ('recognize_loot_count', recognize_loot_count),
            ('recognize_ship_count', recognize_ship_count),
        ):
            if getattr(map, name) is not expected:
                errors.append(f'{name} is not owned by common')
        required_methods = (
            'enter_sortie',
            'select_chapter',
            'select_map',
            'click_chapter_slot',
        )
        missing = [name for name in required_methods if not hasattr(BattlePage, name)]
        if missing:
            errors.append(f'BattlePage missing methods: {missing}')
        required_recognition = (
            '_read_chapter_slots',
            '_read_map',
            '_read_loot_and_ship_count',
            '_read_selected_chapter_y',
        )
        missing_recognition = [
            name for name in required_recognition if not hasattr(recognition, name)
        ]
        if missing_recognition:
            errors.append(f'battle_page recognition missing functions: {missing_recognition}')
        params = list(inspect.signature(BattlePage.enter_sortie).parameters)
        if params != ['self', 'chapter', 'map_num']:
            errors.append(f'enter_sortie parameters are {params}')

    if errors:
        print('[FAIL] ' + '; '.join(errors))
        return 1
    print('[PASS] shared map counter and sortie contracts are valid')
    return 0


if __name__ == '__main__':
    sys.exit(main())
