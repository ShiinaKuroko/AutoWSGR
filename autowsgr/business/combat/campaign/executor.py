"""战役业务执行器。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from autowsgr.business.base import BaseExecutor
from autowsgr.business.combat import CombatResult, run_combat
from autowsgr.business.navigation import goto_page
from autowsgr.common.system.logger import get_logger
from autowsgr.dispatch.registry import register
from autowsgr.types import ConditionFlag, PageName

from .operations import CampaignOperations
from .spec import CAMPAIGN_DAILY_LIMIT, CampaignSpec


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
            save_progress=self._save_fleet_progress,
        )

    def _execute(self) -> CombatResult:
        previous = self.progress.get('_result')
        if previous is not None and not isinstance(previous, CombatResult):
            raise TypeError('任务进度 _result 必须是 CombatResult')

        from autowsgr.business.system.initialize.initialize import initialize

        reuse_page = self.progress.pop('_reuse_campaign_page', False)
        if not isinstance(reuse_page, bool):
            raise TypeError('任务进度 _reuse_campaign_page 必须是布尔值')

        try:
            if not reuse_page:
                initialize(self.ctx)
            if previous is not None:
                self.progress.pop('_result', None)
                self.progress.pop('_campaign_fleet', None)
                return previous

            executed = self._campaign_count()
            if executed >= CAMPAIGN_DAILY_LIMIT:
                result = CombatResult(flag=ConditionFlag.BATTLE_TIMES_EXCEED)
                self._report('stop_after_current', reason=result.flag.value)
                return result

            _log.info(
                '[Campaign] 开始战役任务: {} ({})',
                self.spec.campaign_name,
                self.spec.difficulty,
            )
            self._operations.enter_campaign(self.spec)
            self._wait(0.5)
            page, ship_stats, fleet = self._operations.prepare_battle(
                self.spec,
                reset_fleet=not self._has_fleet_checkpoint(),
            )
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
            _log.info(
                '[Campaign] 进入战斗：阵型配置={}，夜战配置={}',
                self.spec.plan.default_node.formation.name,
                self.spec.plan.default_node.night,
            )
            result = run_combat(
                self.ctx.ctrl,
                self.spec.plan,
                ship_stats=ship_stats,
                ocr=self.ctx.ocr,
                stop_requested=self._stop.is_set,
            )
            result.fleet = fleet
            if result.flag is ConditionFlag.OPERATION_SUCCESS:
                executed += 1
                self.progress['_campaign_completed'] = executed
                self.progress['_result'] = result
                _log.info(
                    '[Campaign] 战斗结束，战役结果: {}，已执行战役次数 {}，剩余次数 {}',
                    result.flag.value,
                    executed,
                    max(CAMPAIGN_DAILY_LIMIT - executed, 0),
                )
                self._report(
                    'battle_done',
                    executed=executed,
                    remaining=max(CAMPAIGN_DAILY_LIMIT - executed, 0),
                )
                self._wait(0.2)
                self.progress.pop('_result', None)
                self.progress.pop('_campaign_fleet', None)
                return result
            if result.flag in {ConditionFlag.BATTLE_TIMES_EXCEED, ConditionFlag.DOCK_FULL}:
                self._report('stop_after_current', reason=result.flag.value)
                return result
            raise RuntimeError(f'战役战斗未成功: {result.flag.value}')
        finally:
            try:
                if not self.progress.get('_reuse_campaign_page', False):
                    goto_page(self.ctx, PageName.MAIN)
            except Exception as error:
                _log.error('[Campaign] 返回首页失败: {}', error)

    def _save_fleet_progress(self, data: dict[str, Any]) -> None:
        self.progress['_campaign_fleet'] = dict(data)

    def _has_fleet_checkpoint(self) -> bool:
        checkpoint = self.progress.get('_campaign_fleet')
        if checkpoint is None:
            return False
        if not isinstance(checkpoint, dict):
            raise TypeError('任务进度 _campaign_fleet 必须是对象')
        if checkpoint.get('stage') not in {'cleared', 'selected', 'complete'}:
            raise ValueError('任务进度 _campaign_fleet.stage 无效')
        return True

    def _campaign_count(self) -> int:
        value = self.progress.get('_campaign_completed', 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise TypeError('任务进度 _campaign_completed 必须是非负整数')
        return value


register('campaign', CampaignExecutor)
