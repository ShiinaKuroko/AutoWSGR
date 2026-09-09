"""决战地图进入后的浮层稳定等待测试。

上层调用：
- pytest：验证进入地图后首帧识别不会抢在浮层动画完成前执行。

下层依赖：
- business.combat.decisive.handlers：提供进入地图状态处理器。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from autowsgr.business.combat.decisive import handlers
from autowsgr.common.types import DecisiveEntryStatus, DecisivePhase


if TYPE_CHECKING:
    import pytest


def test_enter_map_waits_before_first_map_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    """进入地图后先等待动画，再转入地图等待状态。"""
    events: list[object] = []
    battle_page = MagicMock()
    battle_page.read_entry_status.return_value = DecisiveEntryStatus.CHALLENGING
    battle_page.read_stage.return_value = 1
    battle_page.click_enter_map.side_effect = lambda: events.append('enter')
    context = SimpleNamespace(
        _battle_page=battle_page,
        _config=SimpleNamespace(chapter=6),
        _ctrl=MagicMock(),
        _state=SimpleNamespace(stage=None, phase=None),
        _use_last_fleet_attempts=1,
        _wait_deadline=None,
        _resume_mode=True,
    )
    monkeypatch.setattr(handlers.time, 'monotonic', lambda: 100.0)
    monkeypatch.setattr(handlers.time, 'sleep', lambda delay: events.append(('sleep', delay)))

    handlers.DecisivePhaseHandlers._handle_enter_map(context)

    assert events == ['enter', ('sleep', 2.0)]
    assert context._state.phase is DecisivePhase.WAITING_FOR_MAP
