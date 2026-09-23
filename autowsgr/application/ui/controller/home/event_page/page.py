"""模块功能：编排活动地图页面的识别、选项操作、出击和返回流程。

上层调用：
- application.ui.navigation：检查活动地图页面并执行页面返回。
- business.combat.bettle：选择活动节点并进入出征准备。

下层依赖：
- application.ui.controller.home.event_page.constants：提供页面坐标和视觉校准。
- application.ui.controller.home.event_page.recognition：提供页面视觉事实。
- common.vision 与 common.device.interaction：提供页面识别和交互基础能力。

边界：
本模块只编排活动地图页面内状态和操作，不负责跨任务调度或运行时上下文。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Literal

from autowsgr.application.ui.controller.home.event_page import constants, recognition
from autowsgr.common.system.exceptions import ActionFailedError
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.interaction import NavigationError, click_and_wait_for_page
from autowsgr.application.ui.navigation.types import PageMatch


if TYPE_CHECKING:
    import numpy

    from autowsgr.application.ui.controller.context import UIContext


_log = get_logger('ui.home.event_page')


# ── 页面流程参数 ─────────────────────────────────────────────────────────────

_OVERLAY_CLOSE_MAX_ATTEMPTS = 3  # 节点详情浮层关闭的最大点击次数。
_OVERLAY_CLOSE_DELAY_SECONDS = 0.6  # 关闭浮层后等待页面更新的秒数。
_DIFFICULTY_SWITCH_MAX_ATTEMPTS = 2  # 难度切换的总点击尝试次数。
_NAVIGATION_OVERLAY_CLOSE_DELAY_SECONDS = 0.5  # 返回流程关闭浮层后的等待秒数。
_DIFFICULTY_SWITCH_DELAY_SECONDS = 1.0  # 难度切换后等待页面更新的秒数。
_NODE_SELECT_MAX_ATTEMPTS = 10  # 节点选择后确认浮层的最大轮询次数。
_NODE_SELECT_POLL_INTERVAL_SECONDS = 0.25  # 节点浮层确认的轮询间隔秒数。
_ENTRANCE_SWITCH_DELAY_SECONDS = 0.3  # 入口切换后等待页面更新的秒数。
_HOME_NAVIGATION_TIMEOUT_SECONDS = 15.0  # 返回母港主页的最长等待秒数。
_HOME_NAVIGATION_POLL_TIMEOUT_SECONDS = 3.0  # 点击返回后等待主页状态的窗口秒数。
_HOME_NAVIGATION_POLL_INTERVAL_SECONDS = 0.3  # 返回流程确认主页的轮询间隔秒数。


class BaseEventPage:
    """活动地图页面内的 UI 操作控制器。"""

    def __init__(
        self,
        ctx: UIContext,
        event_name: str | None = None,
    ) -> None:
        """保存调用方注入的上下文和活动标识。

        Args:
            ctx: 提供设备控制器的 UI 上下文。
            event_name: 可选活动标识，用于选择活动专属节点布局。
        """
        self._ctx = ctx
        self._ctrl = ctx.ctrl
        self._event_name = event_name

    # ── 页面识别锚点 ─────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: numpy.ndarray) -> PageMatch:
        """检查截图是否属于活动地图页面。

        浮层内的出击按钮、干净页的难度图标和活动标题按优先级提供页面锚点。

        Args:
            screen: 活动地图截图。

        Returns:
            活动地图页面匹配结果。
        """
        name = str(PageName.EVENT_MAP)

        # 浮层内的出击按钮仍能确认活动地图页面，因此优先检查浮层状态。
        button = recognition.read_fight_button_detail(screen)
        if button is not None:
            return PageMatch(name=name, matched=True, score=button.confidence)

        # 干净页面通过难度切换图标确认，标题仅作为低优先级锚点。
        icon_state = recognition.read_difficulty_icon_state(screen)
        if icon_state is not None:
            return PageMatch(name=name, matched=True, score=0.9)
        title = recognition.read_event_title_match(screen)
        if title is not None:
            return PageMatch(
                name=name,
                matched=True,
                score=title.confidence * 0.95,
            )
        return PageMatch(name=name, matched=False, score=0.0)

    # ── 出击页面流程 ─────────────────────────────────────────────────────────────

    def start_fight(
        self,
        map: str,
        entrance: Literal['alpha', 'beta'] | None = None,
        skip_check: bool = False,
    ) -> None:
        """选择活动节点并点击出击，等待进入出征准备页面。

        Args:
            map: 活动地图标识，例如 H1 或 E2。
            entrance: 可选的活动入口标识。
            skip_check: 是否跳过地图和入口参数校验。

        Raises:
            ValueError: 地图或入口标识无效。
            ActionFailedError: 页面选择或状态确认失败。
            NavigationError: 出击后未进入出征准备页面。
        """

        # 1. 校验输入并完成地图难度、节点和入口选择。
        if not skip_check:
            if (
                len(map) != 2
                or map[0] not in ('H', 'E')
                or not map[1].isdigit()
                or int(map[1]) not in constants.NODE_POSITIONS
            ):
                raise ValueError(f'无效的地图标识: {map}')
            if entrance not in ('alpha', 'beta', None):
                raise ValueError(f'无效的入口标识: {entrance}')
            difficulty, node_id = map[0], int(map[1])
            self._close_node_overlay()
            self._select_difficulty(difficulty)
            self._select_node(node_id)
            if entrance is not None:
                self._select_entrance(entrance)

        # Fleet 页面包间接依赖活动页，保持局部导入避免循环依赖。
        from autowsgr.application.ui.controller.fleet import BattlePreparationPage

        # 2. 读取节点详情浮层中的出击按钮位置。
        screen = self._ctrl.screenshot()
        detail = recognition.read_fight_button_detail(screen)
        if detail is not None:
            coord = detail.center
        else:
            # 模板未命中时使用固定坐标，保留进入出征准备页面的兼容路径。
            coord = constants.CLICK_FIGHT_BUTTON
            _log.warning(
                "[UI] 活动地图 → 回退：expected='fight_button', actual='missing', "
                "fallback='fixed_coordinate', result='continue'",
            )

        # 3. 点击出击并确认进入出征准备页面。
        _log.info(
            '[UI] 活动地图 → 出击：map={!r}, entrance={!r}',
            map,
            entrance,
        )
        click_and_wait_for_page(
            self._ctrl,
            click_coord=coord,
            checker=BattlePreparationPage.check_current_page,
            source=PageName.EVENT_MAP,
            target=PageName.BATTLE_PREP,
        )
        _log.info(
            "[UI] 活动地图 → 出击完成：map={!r}, result='success'",
            map,
        )

    # ── 页面返回流程 ─────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """返回母港主页，并避免返回按钮因画面滞后被连续点击。

        浮层可能拦截返回按钮，因此先关闭浮层，再点击返回并确认母港终态。

        Raises:
            NavigationError: 超过页面返回期限后仍未到达母港主页。
        """
        # HomePage 与活动页存在循环依赖，保留局部导入以避免初始化循环。
        from autowsgr.application.ui.controller.home.main_page import HomePage

        # 1. 循环读取页面状态，避免在未知页面重复点击。
        deadline = time.monotonic() + _HOME_NAVIGATION_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            screen = self._ctrl.screenshot()
            if HomePage.check_current_page(screen):
                _log.info("[UI] 活动地图 → 返回主页：result='success'")
                return

            # 2. 先关闭节点详情浮层，解除其对返回按钮的遮挡。
            if recognition.read_fight_button_detail(screen) is not None:
                _log.info("[UI] 活动地图 → 关闭浮层：reason='return_blocked'")
                self._ctrl.click(*constants.CLICK_CLOSE_NODE_OVERLAY)
                time.sleep(_NAVIGATION_OVERLAY_CLOSE_DELAY_SECONDS)
                continue

            # 3. 点击返回并在稳定窗口内确认母港主页终态。
            _log.info("[UI] 活动地图 → 返回主页：action='click'")
            self._ctrl.click(*constants.CLICK_BACK)
            settled = time.monotonic() + _HOME_NAVIGATION_POLL_TIMEOUT_SECONDS
            while time.monotonic() < settled:
                time.sleep(_HOME_NAVIGATION_POLL_INTERVAL_SECONDS)
            if HomePage.check_current_page(self._ctrl.screenshot()):
                _log.info("[UI] 活动地图 → 返回主页：result='success'")
                return
        _log.error(
            "[UI] 活动地图 → 返回主页超时：expected='home', "
            "actual='event_or_unknown', timeout_seconds={}, result='failed'",
            _HOME_NAVIGATION_TIMEOUT_SECONDS,
        )
        raise NavigationError(
            '活动地图: 返回主页面超时 (浮层/返回点击未能逐层退出)',
            screen=self._ctrl.screenshot(),
        )

    # ── 出击流程内部步骤 ───────────────────────────────────────────────────────────

    def _read_difficulty(self) -> str:
        """读取当前活动地图难度。

        Returns:
            当前难度，H 表示困难，E 表示简单。

        Raises:
            ActionFailedError: 无法确认当前难度或当前页面不属于活动地图。
        """
        screen = self._ctrl.screenshot()
        icon_state = recognition.read_difficulty_icon_state(screen)
        if icon_state is not None:
            return icon_state

        # 难度图标缺失时，先确认仍在活动页面再采用简单难度兜底。
        if self.check_current_page(screen):
            _log.warning(
                "[UI] 活动地图 → 降级：expected='difficulty_icon', actual='missing', "
                "fallback='E', result='continue'",
            )
            return 'E'
        raise ActionFailedError('活动地图: 无法识别当前难度且不在活动页面')

    # ── 节点详情浮层 ─────────────────────────────────────────────────────────────

    def _close_node_overlay(self) -> None:
        """关闭节点详情浮层；浮层不存在时直接返回。

        Raises:
            ActionFailedError: 多次点击后浮层仍未关闭。
        """
        screen = self._ctrl.screenshot()

        # 1. 以浮层内的出击按钮作为状态锚点，避免误点基础页面。
        if recognition.read_fight_button_detail(screen) is None:
            return

        # 2. 每次点击后重新截图，确认浮层是否已经关闭。
        for _ in range(_OVERLAY_CLOSE_MAX_ATTEMPTS):
            self._ctrl.click(*constants.CLICK_CLOSE_NODE_OVERLAY)
            time.sleep(_OVERLAY_CLOSE_DELAY_SECONDS)
            screen = self._ctrl.screenshot()
            if recognition.read_fight_button_detail(screen) is None:
                _log.info("[UI] 活动地图 → 关闭浮层：result='success'")
                return

        _log.error(
            "[UI] 活动地图 → 关闭浮层失败：expected='overlay_closed', "
            "actual='overlay_visible', attempt={}, max_attempts={}, result='failed'",
            _OVERLAY_CLOSE_MAX_ATTEMPTS,
            _OVERLAY_CLOSE_MAX_ATTEMPTS,
        )
        raise ActionFailedError('关闭节点详情浮层', '浮层仍未关闭')

    def _select_difficulty(self, target: str) -> None:
        """切换活动地图到目标难度。

        Args:
            target: 目标难度，H 表示困难，E 表示简单。

        Raises:
            ValueError: 目标难度无效。
            ActionFailedError: 重试后仍未切换到目标难度。
        """
        # 1. 校验目标难度并读取当前页面状态。
        if target not in ('H', 'E'):
            raise ValueError(f'无效的活动地图难度: {target}')

        current = self._read_difficulty()
        if current == target:
            _log.debug(
                '[UI] 活动地图 → 跳过难度切换：target={!r}, current={!r}, '
                "reason='already_selected'",
                target,
                current,
            )
            return

        # 2. 点击难度切换并确认目标状态。
        _log.info(
            '[UI] 活动地图 → 切换难度：from={!r}, target={!r}',
            current,
            target,
        )
        for attempt in range(1, _DIFFICULTY_SWITCH_MAX_ATTEMPTS + 1):
            self._ctrl.click(*constants.CLICK_DIFFICULTY)
            time.sleep(_DIFFICULTY_SWITCH_DELAY_SECONDS)
            current = self._read_difficulty()
            if current == target:
                _log.info(
                    "[UI] 活动地图 → 切换难度完成：target={!r}, result='success'",
                    target,
                )
                return

            if attempt < _DIFFICULTY_SWITCH_MAX_ATTEMPTS:
                _log.warning(
                    '[UI] 活动地图 → 重试：expected={!r}, actual={!r}, '
                    "attempt={}, max_attempts={}, reason='difficulty_not_reached', "
                    "fallback='toggle_again', result='retry'",
                    target,
                    current,
                    attempt,
                    _DIFFICULTY_SWITCH_MAX_ATTEMPTS,
                )

        _log.error(
            '[UI] 活动地图 → 切换失败：expected={!r}, actual={!r}, '
            "attempt={}, max_attempts={}, result='failed'",
            target,
            current,
            _DIFFICULTY_SWITCH_MAX_ATTEMPTS,
            _DIFFICULTY_SWITCH_MAX_ATTEMPTS,
        )
        raise ActionFailedError(
            '切换活动地图难度',
            f'未进入 {target} 难度',
        )

    def _select_node(self, node_id: int) -> None:
        """选择地图节点，并等待节点详情浮层的出击按钮出现。

        Args:
            node_id: 活动地图节点编号。

        Raises:
            ValueError: 节点编号不在当前活动地图布局中。
            ActionFailedError: 节点详情浮层未在限定时间内出现。
        """

        # 1. 根据活动布局校验节点并取得点击坐标。
        positions = constants.NODE_POSITIONS_BY_EVENT.get(
            self._event_name,
            constants.NODE_POSITIONS,
        )
        if node_id not in positions:
            raise ValueError(f'无效的活动地图节点: {node_id}')

        # 2. 点击节点并轮询节点详情浮层的出击按钮。
        x, y = positions[node_id]
        _log.info('[UI] 活动地图 → 选节点：node_id={}', node_id)
        self._ctrl.click(x, y)
        for _ in range(_NODE_SELECT_MAX_ATTEMPTS):
            after = self._ctrl.screenshot()
            if recognition.read_fight_button_detail(after) is not None:
                _log.info(
                    "[UI] 活动地图 → 选节点完成：node_id={}, result='success'",
                    node_id,
                )
                return
            time.sleep(_NODE_SELECT_POLL_INTERVAL_SECONDS)
        _log.error(
            '[UI] 活动地图 → 选节点失败：node_id={}, attempt={}, '
            "max_attempts={}, actual='fight_button_missing', result='failed'",
            node_id,
            _NODE_SELECT_MAX_ATTEMPTS,
            _NODE_SELECT_MAX_ATTEMPTS,
        )
        raise ActionFailedError(
            f'活动地图: 选择节点 {node_id} 失败，未出现节点详情浮层',
        )

    def _select_entrance(self, entrance: Literal['alpha', 'beta']) -> None:
        """切换到目标 Alpha 或 Beta 入口；与当前一致时跳过。

        Args:
            entrance: 目标活动入口。

        Raises:
            ValueError: 入口标识无效。
            ActionFailedError: 点击后未确认目标入口。
        """
        # 1. 校验目标入口并确认当前入口状态。
        if entrance not in ('alpha', 'beta'):
            raise ValueError(f'无效的活动入口: {entrance}')

        want_alpha = entrance == 'alpha'
        screen = self._ctrl.screenshot()
        if recognition.read_alpha_entrance_state(screen) == want_alpha:
            _log.debug(
                "[UI] 活动地图 → 跳过入口切换：entrance={!r}, reason='already_selected'",
                entrance,
            )
            return

        # 2. 点击目标入口并确认页面状态。
        coord = constants.CLICK_ENTRANCE_ALPHA if want_alpha else constants.CLICK_ENTRANCE_BETA
        _log.info('[UI] 活动地图 → 切换入口：entrance={!r}', entrance)
        self._ctrl.click(*coord)
        time.sleep(_ENTRANCE_SWITCH_DELAY_SECONDS)
        if recognition.read_alpha_entrance_state(self._ctrl.screenshot()) == want_alpha:
            _log.info(
                "[UI] 活动地图 → 切换入口完成：entrance={!r}, result='success'",
                entrance,
            )
            return

        _log.error(
            '[UI] 活动地图 → 切换入口失败：entrance={!r}, '
            "actual='target_not_confirmed', result='failed'",
            entrance,
        )
        raise ActionFailedError('切换活动入口', f'未进入 {entrance} 入口')
