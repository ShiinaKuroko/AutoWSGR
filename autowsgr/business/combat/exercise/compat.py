"""旧演习入口的兼容适配器。

这里只保留已有 ``ExerciseRunner`` / ``run_exercise`` 调用方需要的薄包装；
新任务统一通过 :class:`ExerciseExecutor` 和 Processor 进入。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.combat import CombatResult
from autowsgr.types import ConditionFlag

from .executor import ExerciseExecutor


if TYPE_CHECKING:
    from autowsgr.context import GameContext


class ExerciseRunner:
    """兼容 API: 挑战全部可挑战对手 (不参与暂停协作)。"""

    def __init__(self, ctx: GameContext, fleet_id: int = 1) -> None:
        self._ctx = ctx
        self._fleet_id = fleet_id

    def run(self) -> list[CombatResult]:
        """执行完整演习, 返回各场结果。"""
        return ExerciseExecutor(self._ctx, {'fleet_id': self._fleet_id}).run()


class ExerciseOnceRunner(ExerciseRunner):
    """兼容 API: 仅挑战一个对手, 无可挑战时返回 SKIP_FIGHT。"""

    def run(self) -> CombatResult:  # type: ignore[override]
        executor = ExerciseExecutor(self._ctx, {'fleet_id': self._fleet_id, 'rivals_limit': 1})
        results = executor.run()
        if not results:
            return CombatResult(flag=ConditionFlag.SKIP_FIGHT)
        return results[0]


def run_exercise(
    ctx: GameContext,
    fleet_id: int = 1,
    rival: int | None = 1,
) -> list[CombatResult]:
    """兼容 API: ``rival=None`` 挑战全部, 指定编号时仅挑战该对手。"""
    if rival is None:
        return ExerciseRunner(ctx, fleet_id).run()
    return ExerciseExecutor(ctx, {'fleet_id': fleet_id, 'rival': rival}).run()
