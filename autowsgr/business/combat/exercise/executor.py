"""演习执行器 — 以单场挑战为基本执行单元 (2026-08 定稿)。

执行模式 (由 rivals_limit 参数区分):
    完整模式 (默认, rivals_limit=None):
        迭代执行单场挑战直至无可挑战对手。一次 Processor 请求就是一轮
        完整演习; 重复次数由请求的 count 字段控制, 不写入 YAML。
    限额模式 (rivals_limit=N):
        累计挑战 N 个对手后即视为完成; N=1 为单场模式。

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
from autowsgr.business.combat.exercise.spec import ExerciseSpec
from autowsgr.business.system.navigate import goto_page
from autowsgr.combat import CombatResult, run_combat
from autowsgr.combat.fleet import exact_fleet_rules
from autowsgr.dispatch.registry import register
from autowsgr.infra.base.ui.interaction import NavigationError
from autowsgr.infra.base.ui.pages.battle_preparation import BattlePreparationPage
from autowsgr.infra.base.ui.pages.battle_preparation.base import RepairStrategy
from autowsgr.infra.base.ui.pages.map import MapPage, MapPanel
from autowsgr.infra.logger import get_logger
from autowsgr.types import ConditionFlag, PageName, RepairMode, ShipDamageState


if TYPE_CHECKING:
    from autowsgr.context import GameContext


_log = get_logger('business.combat.exercise')

# 准备页暂停退出的返回键重试次数 (入场动画抖动时点击可能落空)
_PREP_BACK_RETRIES = 3


class ExerciseExecutor(BaseExecutor):
    """演习执行器: 单场挑战为基本执行单元, 按模式迭代至终止条件。"""

    def __init__(self, ctx: GameContext, params: dict | None = None, **kwargs: Any) -> None:
        super().__init__(ctx, params, **kwargs)
        self.spec = ExerciseSpec.from_params(self.params)
        self.plan = self.spec.plan
        self.fleet_selection = self.spec.fleet_selection
        self.fleet_id = self.fleet_selection.fleet_id
        self.rivals_limit = self.spec.rivals_limit
        """单轮挑战数量上限 (None=完整模式不限; N=限额模式, 1 为单次)。"""
        self.rival = self.spec.rival
        """指定对手编号; ``None`` 表示自动选择。"""
        self._prep_active = False

    # ── 主流程 ─────────────────────────────────────────────────

    def _execute(self) -> list[CombatResult]:
        results: list[CombatResult] = []

        # 每张任务单都从初始化后的首页开始，避免复用过期页面上下文。
        from autowsgr.business.system.initialize.initialize import initialize

        try:
            initialize(self.ctx)
            _log.info(
                '[Exercise] 演习编队加载: 队伍 {}，规则 {}',
                self.fleet_id,
                '已配置'
                if self.fleet_selection.slot_rules or self.fleet_selection.plain_fleet
                else '沿用当前队伍',
            )

            self._goto_exercise_panel()
            self._wait(1.0)  # 断点①: 面板导航完成后

            # 终止条件: 完整模式 — 无可挑战对手; 限额模式 — 配额耗尽。
            while self._has_quota():
                target = self._pick_rival()
                if target is None:
                    break  # 无可挑战对手, 本轮结束
                results.append(self._fight_one(target))
                self._wait(1.0)  # 断点④: 战斗完成后 (强制检查, 含最后一场)
                if not self._has_quota():
                    break  # 配额耗尽, 无需复位面板
                self._goto_exercise_panel()  # 复位面板, 供下一场识别

            _log.info(
                '[Exercise] 演习完成, 本次 {} 场, 累计计数 {}',
                len(results),
                self.progress.get('fought', 0),
            )
            return results
        finally:
            # 任务异常、停止或暂停都不能把设备留在演习链路中；清理错误
            # 只记录，不覆盖原始业务异常。
            try:
                self._return_home()
            except Exception as error:
                _log.error('[Exercise] 返回首页失败: {}', error)

    # ── 基本执行单元: 单场挑战 ─────────────────────────────────

    def _fight_one(self, target: int) -> CombatResult:
        """执行单场挑战: 选择对手 → 编队 → 出征 → 战斗, 完成后计数累加。"""
        map_page = MapPage(self.ctx)
        _log.info('[Exercise] 选择对手：{}号', target)
        map_page.select_exercise_rival(target)
        map_page.enter_exercise_battle()  # 确认弹窗 → 进入出征准备页
        self._prep_active = True
        self._report('rival_confirmed', rival=target)
        self._wait_on_prep(1.0)  # 断点②: 对手确认后 (已进入准备页)

        page = BattlePreparationPage(self.ctx)
        page.select_fleet(self.fleet_id)
        _log.info('[Exercise] 选择队伍：{}', self.fleet_id)
        _log.info('[Exercise] 进入舰队编成')
        self._report('formation_entered', rival=target)
        self._wait_on_prep(0.2)

        slot_rules = self.fleet_selection.slot_rules
        if slot_rules is None and self.fleet_selection.plain_fleet is not None:
            slot_rules = exact_fleet_rules(self.fleet_selection.plain_fleet)
        if slot_rules is not None:
            for slot, rule in enumerate(slot_rules[:6], start=1):
                for option in rule.options:
                    _log.info(
                        '[Exercise] 开始选择 {} 号位舰船: {} ({}校验)',
                        slot,
                        option.name,
                        '宽泛' if option.relaxed_constraints else '严格',
                    )
            changed = page.change_fleet(
                self.fleet_id,
                slot_rules,
                on_event=self._on_fleet_event,
            )
            if not changed:
                raise RuntimeError('演习编队未满足 YAML 规则')
        else:
            _log.info('[Exercise] 当前队伍已满足演习编队（未提供替换规则）')

        self._report('fleet_ready', rival=target)
        self._wait_on_prep(0.5)  # 断点③: 编队完成后 (尚未出征)

        page.apply_supply()
        repair_strategy = self._repair_strategy()
        if repair_strategy is not None:
            page.apply_repair(repair_strategy)

        screen = self.ctx.ctrl.screenshot()
        damage = page.detect_ship_damage(screen)
        ship_stats = [damage.get(i, ShipDamageState.NORMAL) for i in range(6)]

        # 出征前最后一个可交接点。
        self._report('before_start', rival=target)
        self._wait_on_prep(0.2)
        page.start_battle()
        self._prep_active = False
        _log.info('[Exercise] 进入战斗')
        self._report('battle_started', rival=target)
        time.sleep(1.0)  # 战斗进入过渡 — 原子段内, 不响应暂停
        result = self._run_combat(ship_stats)

        # 战斗引擎在停止/SL/船坞满时也可能返回结果对象；这些不是成功的
        # 演习轮次，交给处理器按异常或停止协议收口，不能计入进度。
        if self._stop.is_set():
            self._check_pause()
        if result.flag is not ConditionFlag.OPERATION_SUCCESS:
            raise RuntimeError(f'演习战斗未成功: {result.flag.value}')

        self.progress['fought'] = self.progress.get('fought', 0) + 1
        _log.info('[Exercise] 战斗结束，演习结果: {}', result.flag.value)
        self._report('rival_done', rival=target, fought=self.progress['fought'])
        return result

    def _run_combat(self, ship_stats: list[ShipDamageState]) -> CombatResult:
        """构建 CombatPlan 并执行战斗 (原子操作: 执行期间不响应暂停)。"""
        return run_combat(self.ctx, self.plan, ship_stats=ship_stats)

    def _return_home(self) -> None:
        """从准备页先回地图，再使用共享导航回首页。"""
        if self._prep_active or BattlePreparationPage.is_current_page(self.ctx.ctrl.screenshot()):
            BattlePreparationPage(self.ctx).go_back()
            self._prep_active = False
        goto_page(self.ctx, PageName.MAIN)

    def _repair_strategy(self) -> RepairStrategy | None:
        """将演习计划的修理阈值转换为准备页策略。"""
        modes = self.plan.repair_mode
        if not isinstance(modes, list):
            modes = [modes]
        value = min(mode.value if isinstance(mode, RepairMode) else int(mode) for mode in modes)
        if value <= RepairMode.moderate_damage.value:
            return RepairStrategy.MODERATE
        if value <= RepairMode.severe_damage.value:
            return RepairStrategy.SEVERE
        return None

    def _on_fleet_event(self, event: str, **data: Any) -> None:
        """记录编队细节，并在每次选船完成后交回处理器断点。"""
        if event == 'fleet_validation':
            _log.info(
                '[Exercise] 当前队伍{}满足演习编队',
                '已' if data.get('passed') else '不',
            )
            self._report(event, **data)
        elif event == 'ship_selected':
            option = data.get('option')
            selected = data.get('selected') or '未识别'
            _log.info(
                '[Exercise] 开始替换 {} 号位舰船: {} → {}',
                data.get('slot', '?'),
                getattr(option, 'name', '目标'),
                selected,
            )
            self._report(
                'ship_selected',
                slot=data.get('slot'),
                expected=getattr(option, 'name', None),
                actual=selected,
            )
            self._wait_on_prep(0)
        elif event == 'ship_removed':
            self._report('ship_selected', slot=data.get('slot'), actual=None)
            self._wait_on_prep(0)
        elif event == 'ship_moved':
            _log.info(
                '[Exercise] 开始移动 {} 号位到 {} 号位位置',
                data.get('source', '?'),
                data.get('destination', '?'),
            )
        elif event == 'fleet_result':
            members = [name for name in data.get('members', []) if name]
            _log.info('[Exercise] 舰队编成完毕成员为：{}', '、'.join(members))
            self._report(event, **data)

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
        if self._pause.is_set() or self._stop.is_set():
            time.sleep(seconds)
            page = BattlePreparationPage(self.ctx)
            for attempt in range(_PREP_BACK_RETRIES):
                try:
                    page.go_back()
                    self._prep_active = False
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
