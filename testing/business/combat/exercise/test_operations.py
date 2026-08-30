"""演习页面操作和 OCR 日志的无设备回归。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from autowsgr.combat.fleet import FleetSlotRule, ShipSelector
from autowsgr.infra.base.combat.battle_preparation import BattlePreparationPage
from autowsgr.infra.base.combat.battle_preparation.fleet_change import _change
from autowsgr.infra.base.combat.battle_preparation.fleet_change._detect import FleetSnapshot
from autowsgr.types import ShipType


def _page() -> BattlePreparationPage:
    return BattlePreparationPage(
        SimpleNamespace(
            ctrl=MagicMock(),
            ocr=None,
            ship_ocr=None,
        ),
    )


def _snapshot(name: str | None) -> FleetSnapshot:
    return FleetSnapshot(
        names=[name, None, None, None, None, None],
        occupied=[name is not None, False, False, False, False, False],
        ship_types=[ShipType.SS, None, None, None, None, None],
        ship_levels=[69, None, None, None, None, None],
    )


def test_relaxed_ocr_success_is_logged_as_auto_release() -> None:
    page = _page()
    rule = FleetSlotRule(
        primary=ShipSelector(
            name='U-177',
            ship_types=(ShipType.SS,),
            min_level=69,
            relaxed_constraints=True,
        ),
    )

    with patch.object(_change, '_log') as log:
        page._log_snapshot_debug('LEVEL1', _snapshot('U-177'), [rule], 1)

    messages = [call.args[0] for call in log.info.call_args_list]
    assert '[OCR] 宽泛校验规则生效，自动放行' in messages
    assert any(
        call.args[0] == '[OCR] 目标舰船：{} / {} / {}，识别成功！'
        for call in log.info.call_args_list
    )


def test_ocr_failure_logs_numeric_attempt() -> None:
    page = _page()
    rule = FleetSlotRule(primary=ShipSelector(name='U-177'))

    with patch.object(_change, '_log') as log:
        page._log_snapshot_debug('LEVEL2', _snapshot(None), [rule], 2)

    warning = next(call for call in log.warning.call_args_list if '当前次数' in call.args[0])
    assert warning.args[-1] == 2
