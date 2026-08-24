"""演习执行器 — 以单场挑战为基本执行单元 (2026-08 定稿)。

执行模式 (由 rivals_limit 参数区分):
    完整模式 (默认, rivals_limit=None):
        迭代执行单场挑战直至无可挑战对手; times 为完整流程的
        执行轮数 (YAML times:1 即执行一轮完整演习)。
    限额模式 (rivals_limit=N):
        累计挑战 N 个对手后即视为完成; N=1 为单次模式
        (兼容定时触发器 ExerciseOnceRunner)。

计数粒度: 以单场为计数单位, _fight_one() 每完成一场挑战即将
progress['fought'] 累加一次; 任务被暂停后重跑时计数延续,
不因重新调度而清零或重复统计。

中断恢复协议: 执行器在断点检测到暂停信号 → 返回主页让出控制权 →
处理器执行高优先级任务 → 本任务重新调度, 依据对手挑战状态识别
(已挑战对手呈现置灰) 跳过已完成场次, 继续处理剩余对手, 直至
无可挑战对手后正常结束。

页面流转:
    主页 → goto_page(MAP) → 切换演习面板 → 识别对手状态 → 选择对手
    → 二次确认弹窗 → 出征准备页 (选择编队 + 船损检测) → 出征
    → run_combat(EXERCISE) → 结算 → 返回演习面板 → 下一对手 → 主页。

可中断断点 (暂停检查内置于 _wait, 处理器置位信号后在最近断点生效):
    ① 面板导航完成后 (panel_ready 之后的等待点)
    ② 对手确认后 (rival_confirmed 之后的等待点, 已进入准备页)
    ③ 编队完成后 (fleet_ready 之后的等待点, 尚未出征, 状态可完全回退)
    ④ 每场战斗完成后 (rival_done 之后的等待点, 强制检查, 含最后一场)
    ②③ 位于出征准备页 (不在导航图内), 暂停时先 go_back 退回地图页再回主页
    (见 _wait_on_prep)。

编队策略: FleetPolicy(select=True, fleets=(1,2,3,4)), 见 fleet_policy.py。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from autowsgr.business.base import BaseExecutor
from autowsgr.business.system.navigate import goto_page
from autowsgr.combat import CombatMode, CombatPlan, CombatResult, NodeDecision, run_combat
from autowsgr.dispatch.registry import register
from autowsgr.infra.base.ui.pages.map import MapPage, MapPanel
from autowsgr.infra.logger import get_logger
from autowsgr.ops.startup import recover_to_main_or_restart
from autowsgr.types import ConditionFlag, Formation, PageName, ShipDamageState
# 出征准备页尚未迁入 infra/base/ui/pages (待迁移), 暂走 ui.battle
from autowsgr.ui.battle import BattlePreparationPage
from autowsgr.ui.utils import NavigationError


if TYPE_CHECKING:
    from autowsgr.context import GameContext


_log = get_logger('business.combat.exercise')

# 准备页暂停退出的返回键重试次数 (入场动画抖动时点击可能落空)
_PREP_BACK_RETRIES = 3


class ExerciseExecutor(BaseExecutor):
    """演习执行器: 单场挑战为基本执行单元, 按模式迭代至终止条件。"""

    def __init__(self, ctx: GameContext, params: dict | None = None, **kwargs: Any) -> None:
        super().__init__(ctx, params, **kwargs)
        self.fleet_id = int(self.params.get('fleet_id', 1))
        self.times = int(self.params.get('times', 1))
        """完整流程执行轮数 (YAML times, 默认 1)。"""
        self.rivals_limit = self.params.get('rivals_limit')
        """单轮挑战数量上限 (None=完整模式不限; N=限额模式, 1 为单次)。"""
        self.rival = self.params.get('rival')
        """指定对手编号 (兼容 run_exercise 的 rival 参数; None 为自动选择)。"""

    # ── 主流程 ─────────────────────────────────────────────────

    def _execute(self) -> list[CombatResult]:
        results: list[CombatResult] = []

        # 确保游戏处于可识别页面 (页面异常时先恢复/重启)
        recover_to_main_or_restart(self.ctx, self.ctx.config.account.game_app)

        self._goto_exercise_panel()
        self._wait(1.0)  # 断点①: 面板导航完成后

        for _ in range(self.times):
            # 终止条件: 完整模式 — 无可挑战对手; 限额模式 — 配额耗尽
            while self._has_quota():
                target = self._pick_rival()
                if target is None:
                    break  # 无可挑战对手, 本轮结束
                results.append(self._fight_one(target))
                self._wait(1.0)  # 断点④: 战斗完成后 (强制检查, 含最后一场)
                if not self._has_quota():
                    break  # 配额耗尽, 无需复位面板
                self._goto_exercise_panel()  # 复位面板, 供下一场识别

        goto_page(self.ctx, PageName.MAIN)  # 锚点: 终态返回主页
        _log.info('[Exercise] 演习完成, 本次 {} 场, 累计计数 {}',
                  len(results), self.progress.get('fought', 0))
        return results

    # ── 基本执行单元: 单场挑战 ─────────────────────────────────

    def _fight_one(self, target: int) -> CombatResult:
        """执行单场挑战: 选择对手 → 编队 → 出征 → 战斗, 完成后计数累加。"""
        map_page = MapPage(self.ctx)
        _log.info('[Exercise] 挑战对手 {}', target)
        map_page.select_exercise_rival(target)
        map_page.enter_exercise_battle()  # 确认弹窗 → 进入出征准备页
        self._report('rival_confirmed', rival=target)
        self._wait_on_prep(1.0)  # 断点②: 对手确认后 (已进入准备页)

        page = BattlePreparationPage(self.ctx)
        page.select_fleet(self.fleet_id)
        self._report('fleet_ready', rival=target)
        self._wait_on_prep(0.5)  # 断点③: 编队完成后 (尚未出征)

        screen = self.ctx.ctrl.screenshot()
        damage = page.detect_ship_damage(screen)
        ship_stats = [damage.get(i, ShipDamageState.NORMAL) for i in range(6)]

        page.start_battle()
        time.sleep(1.0)  # 战斗进入过渡 — 原子段内, 不响应暂停
        result = self._run_combat(ship_stats)

        self.progress['fought'] = self.progress.get('fought', 0) + 1
        self._report('rival_done', rival=target, fought=self.progress['fought'])
        return result

    def _run_combat(self, ship_stats: list[ShipDamageState]) -> CombatResult:
        """构建 CombatPlan 并执行战斗 (原子操作: 执行期间不响应暂停)。"""
        plan = CombatPlan(
            name='演习',
            mode=CombatMode.EXERCISE,
            default_node=NodeDecision(formation=Formation.single_column, night=True),
        )
        return run_combat(self.ctx, plan, ship_stats=ship_stats)

    # ── 辅助方法 ───────────────────────────────────────────────

    def _wait_on_prep(self, seconds: float) -> None:
        """准备页断点 (②③) 的等待: 暂停时先退出准备页再走标准协议。

        出征准备页不在页面注册表/导航图中 (单向中转页, 见
        combat-domain-structure 文档), 标准 ``_check_pause`` 从该页直接
        ``goto_page(MAIN)`` 会因页面识别漂移 (准备页被误判为活动页) 进入
        活动页的浮层关闭死循环。暂停信号到来时先显式 ``go_back``
        (准备页 → 地图页, 自带到达验证), 再走标准暂停协议回主页让路。

        入场动画: 正常路径的 ``_wait`` 本就会等待 *seconds* 让准备页稳定;
        暂停路径不能跳过这段等待, 否则返回键点击会落在动画中 (实机
        2026-08-25: 入场后约 1 秒内点击被吞), 故先等同样时长再点返回,
        失败重试至多 3 次 (动画抖动时点击可能落空)。
        """
        if self._pause.is_set():
            time.sleep(seconds)
            page = BattlePreparationPage(self.ctx)
            for attempt in range(_PREP_BACK_RETRIES):
                try:
                    page.go_back()
                    break
                except NavigationError:
                    if attempt == _PREP_BACK_RETRIES - 1:
                        raise
                    time.sleep(1.0)
        self._wait(seconds)

    def _goto_exercise_panel(self) -> None:
        """导航至出征页的演习面板。"""
        goto_page(self.ctx, PageName.MAP)
        MapPage(self.ctx).switch_panel(MapPanel.EXERCISE)
        self._report('panel_ready')

    def _has_quota(self) -> bool:
        """配额检查: 完整模式恒为 True; 限额模式在累计计数达到上限前为 True。"""
        return self.rivals_limit is None or self.progress.get('fought', 0) < self.rivals_limit

    def _pick_rival(self) -> int | None:
        """选择下一个可挑战对手 (基于截图识别; 指定模式仅校验指定编号)。"""
        rivals = MapPage(self.ctx).get_exercise_rival_status().rivals
        if self.rival is not None:
            return self.rival if rivals[self.rival - 1] else None
        return next((i for i, ok in enumerate(rivals, start=1) if ok), None)


register('exercise', ExerciseExecutor)


# ═══════════════════════════════════════════════════════════════════════════════
# 兼容层 (examples / scheduler 触发器 / server HTTP 接口 / 既有测试)
# ═══════════════════════════════════════════════════════════════════════════════


class ExerciseRunner:
    """兼容 API: 挑战全部可挑战对手 (不参与暂停协作)。"""

    def __init__(self, ctx: GameContext, fleet_id: int = 1) -> None:
        self._ctx = ctx
        self._fleet_id = fleet_id

    def run(self) -> list[CombatResult]:
        """执行完整演习, 返回各场结果。"""
        return ExerciseExecutor(self._ctx, {'fleet_id': self._fleet_id}).run()


class ExerciseOnceRunner(ExerciseRunner):
    """兼容 API: 仅挑战一个对手, 无可挑战时返回 SKIP_FIGHT (定时触发器使用)。"""

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
    """兼容 API 便捷函数: rival=None 挑战全部, 指定编号时仅挑战该对手。"""
    if rival is None:
        return ExerciseRunner(ctx, fleet_id).run()
    return ExerciseExecutor(ctx, {'fleet_id': fleet_id, 'rival': rival}).run()
