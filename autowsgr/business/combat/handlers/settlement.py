"""战斗战果和掉落的业务解释。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from autowsgr.application.combat import (
    CombatPhase,
    detect_mvp,
    detect_result_grade,
    detect_ship_stats,
    get_ship_drop,
)
from autowsgr.application.combat.history import CombatEvent, CombatHistory, EventType, FightResult
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import ConditionFlag, ShipDamageState


if TYPE_CHECKING:
    from autowsgr.common.device import AndroidController
    from autowsgr.common.vision import OCREngine


_log = get_logger('combat')


class CombatSettlementMixin:
    """识别战果并记录战斗业务结果。"""

    _device: AndroidController
    _ocr: OCREngine | None
    _plan: Any
    _node: str
    _ship_stats: list[ShipDamageState]
    _history: CombatHistory

    # ── 战果解释 ─────────────────────────────────────────────

    def _handle_result(self) -> ConditionFlag:
        """识别战果并记录业务结果。"""
        time.sleep(1.5)
        grade = detect_result_grade(self._device)
        self._ship_stats = detect_ship_stats(self._device, self._ship_stats)
        mvp = detect_mvp(self._device.screenshot())
        fight_result = FightResult(
            node=self._node,
            mvp=mvp,
            grade=grade,
            ship_stats=self._ship_stats[:],
        )
        self._history.add(
            CombatEvent(
                event_type=EventType.RESULT,
                node=self._node,
                result=grade,
                ship_stats=self._ship_stats[:],
                extra={'mvp': mvp},
            )
        )
        _log.info('[Combat] 战果: {} 节点: {}', fight_result, self._node)
        if self._plan.collect_result_info:
            self._click_result_until_closed(CombatPhase.RESULT)
        else:
            self._click_result_until_closed(
                CombatPhase.RESULT,
                pass_through=(CombatPhase.EXP_SETTLEMENT,),
            )
        return ConditionFlag.FIGHT_CONTINUE

    def _capture_get_ship(self) -> str | None:
        """识别并幂等记录掉落舰船。"""
        existing = self._history.get_event(EventType.GET_SHIP, self._node)
        if existing is not None:
            return existing.result or None
        ship_name = get_ship_drop(self._device, self._ocr)
        if not ship_name:
            return None
        _log.info('[Combat] 获得舰船: {}', ship_name)
        self._history.add(
            CombatEvent(
                event_type=EventType.GET_SHIP,
                node=self._node,
                result=ship_name,
            )
        )
        return ship_name


__all__ = ['CombatSettlementMixin']
