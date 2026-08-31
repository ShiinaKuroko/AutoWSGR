"""战役业务执行器。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from autowsgr.business.base import BaseExecutor
from autowsgr.business.combat import CombatResult, run_combat
from autowsgr.common.system.logger import get_logger
from autowsgr.dispatch.registry import register
from autowsgr.types import ConditionFlag

from .operations import CampaignOperations
from .spec import CampaignSpec


if TYPE_CHECKING:
    from autowsgr.application.runtime import RuntimeContext as GameContext


_log = get_logger('business.combat.campaign')


class CampaignExecutor(BaseExecutor):
    """执行一次战役；重复次数由 Processor 的 count 控制。"""

    def __init__(self, ctx: GameContext, params: dict | None = None, **kwargs: Any) -> None:
        super().__init__(ctx, params, **kwargs)
        self.spec = CampaignSpec.from_params(self.params)
        self._operations = CampaignOperations(
            self.ctx,
            wait=self._wait,
            report=self._report,
        )

    def _execute(self) -> CombatResult:
        previous = self.progress.get('_result')
        if previous is not None and not isinstance(previous, CombatResult):
            raise TypeError('任务进度 _result 必须是 CombatResult')

        from autowsgr.business.system.initialize.initialize import initialize

        try:
            initialize(self.ctx)
            if previous is not None:
                self.progress.pop('_result', None)
                return previous

            _log.info(
                '[Campaign] 战役开始: {} ({}), 阵型={}, 夜战={}',
                self.spec.campaign_name,
                self.spec.difficulty,
                self.spec.plan.default_node.formation.name,
                self.spec.plan.default_node.night,
            )
            self._operations.enter_campaign(self.spec)
            self._wait(0.5)
            page, ship_stats, fleet = self._operations.prepare_battle(self.spec)
            self._report('before_start')
            self._wait(0.2)

            if not self._operations.start_battle(page):
                result = CombatResult(
                    flag=ConditionFlag.BATTLE_TIMES_EXCEED,
                    ship_stats=ship_stats,
                    fleet=fleet,
                )
                self._report('stop_after_current', reason=result.flag.value)
                return result

            time.sleep(1.0)
            result = run_combat(
                self.ctx.ctrl,
                self.spec.plan,
                ship_stats=ship_stats,
                ocr=self.ctx.ocr,
                stop_requested=self._stop.is_set,
            )
            result.fleet = fleet
            if result.flag is ConditionFlag.OPERATION_SUCCESS:
                self.progress['_result'] = result
                self._report('battle_done')
                self._wait(0.2)
                self.progress.pop('_result', None)
                _log.info('[Campaign] 战斗结束，战役结果: {}', result.flag.value)
                return result
            if result.flag in {ConditionFlag.BATTLE_TIMES_EXCEED, ConditionFlag.DOCK_FULL}:
                self._report('stop_after_current', reason=result.flag.value)
                return result
            raise RuntimeError(f'战役战斗未成功: {result.flag.value}')
        finally:
            try:
                self._operations.return_home()
            except Exception as error:
                _log.error('[Campaign] 返回首页失败: {}', error)


register('campaign', CampaignExecutor)
