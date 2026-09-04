"""通用战斗阶段处理。

本模块只负责阶段分发、通用点击、页面推进和终态动作；战斗业务规则由上层
提供的处理器实现。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from autowsgr.application.combat.actions import (
    click_fight_condition,
    click_image,
    click_night_battle,
    click_result,
    click_skip_missile_animation,
)
from autowsgr.application.combat.engine.state import CombatPhase
from autowsgr.application.combat.history import CombatEvent, CombatHistory, EventType
from autowsgr.application.combat.recognition import SHIP_DROP_PAGE_SIGNATURE
from autowsgr.application.combat.recognizer import CombatRecognizer
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import ConditionFlag
from autowsgr.common.vision.resources import TemplateKey


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.device import AndroidController


_log = get_logger('combat')


# ── 状态 → 处理器方法名映射  ────────────────────────────────────────────────

_PHASE_HANDLERS: dict[CombatPhase, str] = {
    CombatPhase.FIGHT_CONDITION: '_handle_fight_condition',
    CombatPhase.SPOT_ENEMY_SUCCESS: '_handle_spot_enemy',
    CombatPhase.FORMATION: '_handle_formation',
    CombatPhase.MISSILE_ANIMATION: '_handle_missile_animation',
    CombatPhase.FIGHT_PERIOD: '_handle_fight_period',
    CombatPhase.NIGHT_PROMPT: '_handle_night_prompt',
    CombatPhase.RESULT: '_handle_result',
    CombatPhase.EXP_SETTLEMENT: '_handle_exp_settlement',
    CombatPhase.GET_SHIP: '_handle_get_ship',
    CombatPhase.PROCEED: '_handle_proceed',
    CombatPhase.FLAGSHIP_SEVERE_DAMAGE: '_handle_flagship_severe_damage',
    CombatPhase.DOCK_FULL: '_handle_dock_full',
}


class CombatPhaseHandlersMixin:
    """通用战斗阶段处理 Mixin。

    为 ``CombatEngine`` 提供 ``_make_decision`` 及所有 ``_handle_*`` 方法。

    约定: 本 Mixin 假设宿主类具有以下属性::

        _device: AndroidController
        _plan: Any
        _node: str
        _last_action: str
        _ship_stats: list[Any]
        _history: CombatHistory
        _node_count: int
        _recognizer: CombatRecognizer
    """

    # 类型提示 (供 IDE/mypy 在 Mixin 上下文使用)
    _device: AndroidController
    _plan: Any
    _node: str
    _last_action: str
    _ship_stats: list[Any]
    _history: CombatHistory
    _recognizer: CombatRecognizer
    _node_count: int

    def _make_decision(self, phase: CombatPhase) -> ConditionFlag:
        """根据当前状态做出决策并执行操作。

        每个状态通过 ``_PHASE_HANDLERS`` 映射到对应的处理器方法；
        处理器执行完毕后，若当前状态是终止阶段则返回 ``FIGHT_END``。

        Parameters
        ----------
        phase:
            当前识别到的战斗状态。

        Returns
        -------
        ConditionFlag
        """
        # ── 派发处理器 ──
        handler_name = _PHASE_HANDLERS.get(phase)
        if handler_name is not None:
            result = getattr(self, handler_name)()
        else:
            result = ConditionFlag.FIGHT_CONTINUE

        # ── 终止态检查 ──
        if phase == self._plan.end_phase:
            self._history.add(
                CombatEvent(
                    event_type=EventType.AUTO_RETURN,
                    node=self._node,
                    action='正常',
                )
            )
            return ConditionFlag.FIGHT_END

        return result

    # ── 各状态处理器 ─────────────────────────────────────────────────────────

    def _handle_fight_condition(self) -> ConditionFlag:
        """处理战况选择。
        TODO: 需测试
        """
        condition = self._plan.fight_condition
        click_fight_condition(self._device, condition)
        self._last_action = str(condition.value)

        self._history.add(
            CombatEvent(
                event_type=EventType.FIGHT_CONDITION,
                node=self._node,
                action=str(condition.value),
            )
        )
        return ConditionFlag.FIGHT_CONTINUE

    def _handle_missile_animation(self) -> ConditionFlag:
        """跳过导弹支援动画。"""
        _log.info('[Combat] 跳过导弹支援动画')
        click_skip_missile_animation(self._device)
        self._last_action = 'skip_animation'
        return ConditionFlag.FIGHT_CONTINUE

    def _handle_fight_period(self) -> ConditionFlag:
        """处理战斗进行中。"""
        decision = self._get_current_decision()
        if decision.SL_when_enter_fight:
            self._history.add(
                CombatEvent(
                    event_type=EventType.ENTER_FIGHT,
                    node=self._node,
                    action='SL',
                )
            )
            return ConditionFlag.SL
        return ConditionFlag.FIGHT_CONTINUE

    def _handle_night_prompt(self) -> ConditionFlag:
        """处理夜战选择。"""
        decision = self._get_current_decision()
        pursue = decision.night

        _log.info('[Combat] 夜战选择: {}', '追击' if pursue else '撤退')
        click_night_battle(self._device, pursue=pursue)
        self._last_action = 'yes' if pursue else 'no'

        self._history.add(
            CombatEvent(
                event_type=EventType.NIGHT_BATTLE,
                node=self._node,
                action='追击' if pursue else '撤退',
            )
        )
        return ConditionFlag.FIGHT_CONTINUE

    def _click_result_until_closed(
        self,
        phase: CombatPhase,
        *,
        attempts: int = 6,
        interval: float = 0.3,
        polls: int = 4,
        pass_through: tuple[CombatPhase, ...] = (),
    ) -> None:
        """点击战果类页面继续，并验证已到达**已知后继状态**。

        验证判据是到达验证而非"原页面签名消失"——点击 RESULT 战果页后,
        游戏先进入**经验结算子页** (逐舰船经验, 对应 CombatPhase.EXP_SETTLEMENT):
        若以"RESULT 消失"为成功判据, 复检会在经验页误判成功提前返回,
        引擎随后等待 PROCEED/GET_SHIP 等状态全部落空
        (实机 2026-08-15: 状态识别超时 → 恢复失败 → 强制重启)。

        **快速点击 + 复检轮询**: 点击后每 *interval* 秒截图识别一次
        (最多 *polls* 次), 在 ``[phase] + pass_through + 后继状态`` 集合上判定:
          - 命中后继 → 成功返回;
          - 命中 *pass_through* 中的页面 (如快速穿行模式的经验页) →
            视为未到达, 继续点击跳过;
          - 命中 *phase* → 点击被动画吞掉, 立即重试点击 (重试即动画等待);
           - 识别不到 (过渡帧/页面渐变中) → **只等待不点击**: 对切换中的
             页面盲目连点会穿透中间页, 落点若是 PROCEED 对话框还可能误触
             按钮。轮询窗口耗尽仍认不出则交由外层状态机确认, 不再盲目点击。

        Parameters
        ----------
        phase:
            待关闭页面的状态签名 (RESULT / GET_SHIP)。
        attempts:
            最大点击次数。
        interval:
            复检轮询间隔 (秒)。
        polls:
            每次点击后的复检轮询上限 (过渡帧最长等待 attempts x interval x polls)。
        pass_through:
            识别到即**继续点击跳过**的过渡页 (快速穿行模式的 EXP_SETTLEMENT)。
        """
        successors = self._result_successors(phase)
        candidates = [phase, *pass_through, *successors]
        for attempt in range(1, attempts + 1):
            click_result(self._device)
            for _ in range(polls):
                time.sleep(interval)
                screen = self._device.screenshot()
                current = self._recognizer.identify_current(screen, candidates)
                if current is None:
                    # 过渡帧: 只等待, 不点击 (防穿透/误触)。GET_SHIP 模板
                    # 可能因页面动画/字体渲染未命中, 用掉落页像素签名兜底探测,
                    # 防止快速穿行把掉落页直接点过去导致漏统计。
                    if CombatPhase.GET_SHIP in candidates and self._is_get_ship_page(screen):
                        _log.debug(
                            '[Combat] {} 过渡帧命中掉落页像素签名, 捕获掉落',
                            phase.name,
                        )
                        self._capture_get_ship()
                        return
                    continue
                if current in pass_through:
                    _log.debug(
                        '[Combat] {} 到达过渡页 {} (第 {} 次点击), 继续点击跳过',
                        phase.name,
                        current.name,
                        attempt,
                    )
                    break  # 过渡页: 继续点击 (与"被吞"同路径)
                if current == phase:
                    _log.warning(
                        '[Combat] {} 页面未关闭 (第 {} 次点击), 延迟重试', phase.name, attempt
                    )
                    break  # 确认被吞 → 重试点击
                if current == CombatPhase.GET_SHIP:
                    # 点击穿透到掉落页: 立即幂等捕获掉落, 不依赖主循环重新派发
                    self._capture_get_ship()
                _log.debug('[Combat] {} 已推进到 {}', phase.name, current.name)
                return
            else:
                # 整个轮询窗口都无法识别 → 交外层状态机继续确认, 避免跳过掉落页
                _log.debug(
                    '[Combat] {} 点击后持续无法识别 (第 {} 次), 等待外层状态机确认',
                    phase.name,
                    attempt,
                )
                return
        _log.error('[Combat] {} 页面点击 {} 次仍未推进, 继续执行', phase.name, attempts)

    def _result_successors(self, phase: CombatPhase) -> list[CombatPhase]:
        """返回战果类页面点击后的**合法落点集合** (到达验证候选)。

        比 state.py 转移图宽: 转移图按真实流转建模, 此集合额外包含穿透
        场景 — 快速点击下连点两击可能跳过中间页 (如 RESULT 点击穿透到
        GET_SHIP), 复检把它们都认出来即可提前停止点击, 交引擎主循环按
        当前页继续。

        慢速 (collect_result_info=True): RESULT 之后含经验结算页 (作为
        到达点逐页推进); 快速: 经验页是 pass_through 过渡页, 不在到达集。

        RESULT 之后: PROCEED / 终态页 / GET_SHIP / 旗舰大破 (+经验页, 慢速);
        EXP_SETTLEMENT 之后: 同上但去掉 EXP_SETTLEMENT 自身;
        GET_SHIP 之后: 同上但去掉 GET_SHIP 自身。
        """
        successors = [CombatPhase.PROCEED, CombatPhase.FLAGSHIP_SEVERE_DAMAGE]
        end_phase = self._plan.end_phase
        if end_phase is not None:
            successors.append(end_phase)
        if phase == CombatPhase.RESULT:
            successors.append(CombatPhase.GET_SHIP)
            if self._plan.collect_result_info:
                successors.append(CombatPhase.EXP_SETTLEMENT)
        elif phase == CombatPhase.EXP_SETTLEMENT:
            successors.append(CombatPhase.GET_SHIP)
        return successors

    def _handle_exp_settlement(self) -> ConditionFlag:
        """处理经验结算子页 — 点击继续推进到掉落/前进/终态页。"""
        self._click_result_until_closed(CombatPhase.EXP_SETTLEMENT)
        return ConditionFlag.FIGHT_CONTINUE

    def _handle_get_ship(self) -> ConditionFlag:
        """处理获取舰船 — 幂等捕获掉落并关闭页面。"""
        self._capture_get_ship()
        self._click_result_until_closed(CombatPhase.GET_SHIP)
        return ConditionFlag.FIGHT_CONTINUE

    def _is_get_ship_page(self, screen: np.ndarray) -> bool:
        """用掉落页像素签名兜底识别过渡帧。"""
        return CombatRecognizer._match_pixel(screen, SHIP_DROP_PAGE_SIGNATURE)

    def _handle_flagship_severe_damage(self) -> ConditionFlag:
        """处理旗舰大破。"""
        _log.info('[Combat] 旗舰大破, 强制回港')
        click_image(self._device, TemplateKey.FLAGSHIP_DAMAGE, 2.0)
        time.sleep(0.25)

        self._history.add(
            CombatEvent(
                event_type=EventType.FLAGSHIP_DAMAGE,
                node=self._node,
                action='回港',
            )
        )
        return ConditionFlag.FIGHT_END

    def _handle_dock_full(self) -> ConditionFlag:
        """处理船坞已满弹窗 — 返回 DOCK_FULL 标志交由上层处理。"""
        _log.warning('[Combat] 检测到船坞已满，战斗无法开始')
        self._history.add(
            CombatEvent(
                event_type=EventType.AUTO_RETURN,
                node=self._node,
                action='船坞已满',
            )
        )
        return ConditionFlag.DOCK_FULL

    def _get_current_decision(self) -> Any:
        """由业务宿主提供当前节点的战斗决策。"""
        raise NotImplementedError

    def _capture_get_ship(self) -> str | None:
        """由业务宿主提供掉落结果记录。"""
        raise NotImplementedError


__all__ = ['CombatPhaseHandlersMixin']
