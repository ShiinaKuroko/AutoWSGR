"""模块功能：执行活动地图页面的识别、选项操作、出击和页面返回。

上层调用：
- application.ui.controller.home.main_page.page：取得活动页面检查器。
- application.ui.navigation.event：确认活动页面到达。
- business.combat.bettle.normal_fight：选择活动节点并进入出征准备。
- testing.ui：验证活动页面识别和操作。

下层依赖：
- application.ui.controller.home.event_page.constants：提供活动页面私有校准。
- common.ui.interaction：等待出征准备页面或执行页面回退。
- common.vision：执行模板和像素状态识别。

活动页面没有 OCR 文本规则，因此本模块不拆分 recognition.py；模板匹配属于页面
状态检查，仍由 page.py 负责。活动出征返回澡堂由导航服务提供专用路线。
"""

from __future__ import annotations

import time
from functools import lru_cache
from typing import TYPE_CHECKING, Literal

from autowsgr.application.ui.controller.home.event_page.constants import (
    CLICK_BACK,
    CLICK_CLOSE_NODE_OVERLAY,
    CLICK_DIFFICULTY,
    CLICK_ENTRANCE_ALPHA,
    CLICK_ENTRANCE_BETA,
    CLICK_FIGHT_BUTTON,
    ENTRANCE_ALPHA_COLOR,
    ENTRANCE_ALPHA_PROBE,
    ENTRANCE_ALPHA_TOLERANCE,
    FIGHT_BUTTON_ROI,
    NODE_POSITIONS,
    NODE_POSITIONS_BY_EVENT,
)
from autowsgr.common.system.exceptions import ActionFailedError
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page
from autowsgr.common.vision import (
    ImageChecker,
    ImageMatchDetail,
    PageMatch,
    PixelChecker,
)
from autowsgr.common.vision.resources.pages.event import (
    event_difficulty_easy_templates,
    event_difficulty_hard_templates,
    event_fight_button_templates,
    event_map_title_templates,
)


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext
    from autowsgr.common.vision import ImageTemplate


_log = get_logger('ui')


class BaseEventPage:
    """活动地图页面内的 UI 操作控制器。

    Args:
    ctx:
        由调用方注入的运行时 UI 上下文。
    event_name:
        可选活动标识，用于选择活动专属节点布局。
    """

    def __init__(
        self,
        ctx: GameContext,
        event_name: str | None = None,
    ) -> None:
        """保存页面操作所需的上下文和设备引用。"""
        self._ctx = ctx
        self._ctrl = ctx.ctrl
        self._event_name = event_name

    # ── 页面检查 ──────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """检查截图是否属于活动地图页面，包括节点详情浮层状态。

        出击按钮、难度切换图标和活动标题按置信度优先级作为页面锚点。出击按钮
        可见时说明节点详情浮层打开，但仍属于活动地图页面。
        """
        name = str(PageName.EVENT_MAP)
        button = BaseEventPage._fight_button_detail(screen)
        if button is not None:
            return PageMatch(name=name, matched=True, score=button.confidence)
        icon_state = BaseEventPage._read_difficulty_icon_state(screen)
        if icon_state is not None:
            return PageMatch(name=name, matched=True, score=0.9)
        title = ImageChecker.find_any(screen, _get_event_title_templates(), confidence=0.8)
        if title is not None:
            return PageMatch(name=name, matched=True, score=title.confidence * 0.95)
        return PageMatch(name=name, matched=False, score=0.0)

    # ── 页面状态读取 ──────────────────────────────────────────────────────

    def read_difficulty(self) -> str:
        """读取当前活动地图难度，返回 H 或 E。"""
        screen = self._ctrl.screenshot()
        icon_state = self._read_difficulty_icon_state(screen)
        if icon_state is not None:
            return icon_state
        if self.check_current_page(screen):
            _log.info('[UI] 活动地图: 未检测到难度切换图标, 判定为简单')
            return 'E'
        raise ActionFailedError('活动地图: 无法识别当前难度且不在活动页面')

    # ── 节点详情浮层 ──────────────────────────────────────────────────────

    def close_node_overlay(self) -> None:
        """关闭节点详情浮层；浮层不存在时直接返回。"""
        screen = self._ctrl.screenshot()
        if self._fight_button_detail(screen) is None:
            return
        for _ in range(3):
            self._ctrl.click(*CLICK_CLOSE_NODE_OVERLAY)
            time.sleep(0.6)
            screen = self._ctrl.screenshot()
            if self._fight_button_detail(screen) is None:
                _log.info('[UI] 活动地图: 已关闭残留关卡浮层')
                return
        _log.warning('[UI] 活动地图: 关卡浮层点击 3 次未关闭')

    # ── 页面选项 ──────────────────────────────────────────────────────────

    def select_difficulty(self, target: str) -> None:
        """切换活动地图到目标难度 H 或 E。"""
        current = self.read_difficulty()
        if current == target:
            _log.debug('[UI] 活动地图: 当前已是 {} 难度', target)
            return

        _log.info('[UI] 活动地图: 切换难度 {} -> {}', current, target)
        self._ctrl.click(*CLICK_DIFFICULTY)
        time.sleep(1.0)
        new_diff = self.read_difficulty()
        if new_diff != target:
            _log.warning(
                '[UI] 活动地图: 难度切换验证失败 (期望 {}, 实际 {}), 重试',
                target,
                new_diff,
            )
            self._ctrl.click(*CLICK_DIFFICULTY)
            time.sleep(1.0)

    def select_node(self, node_id: int) -> None:
        """选择地图节点，并等待节点详情浮层的出击按钮出现。"""
        positions = NODE_POSITIONS_BY_EVENT.get(self._event_name, NODE_POSITIONS)
        x, y = positions[node_id]
        _log.debug('[UI] 活动地图: 选择节点 {}', node_id)
        self._ctrl.click(x, y)
        for _ in range(10):
            after = self._ctrl.screenshot()
            if self._fight_button_detail(after) is not None:
                break
            time.sleep(0.25)
        else:
            raise ActionFailedError(f'活动地图: 选择节点 {node_id} 失败，未出现节点详情浮层')

    def select_entrance(self, entrance: Literal['alpha', 'beta']) -> None:
        """切换到目标 Alpha 或 Beta 入口；与当前一致时跳过。"""
        want_alpha = entrance == 'alpha'
        if self._check_alpha_entrance() == want_alpha:
            _log.debug('[UI] 活动地图: 入口已为 {}, 无需切换', entrance)
            return
        coord = CLICK_ENTRANCE_ALPHA if want_alpha else CLICK_ENTRANCE_BETA
        _log.info('[UI] 活动地图: 切换入口 -> {}', entrance)
        self._ctrl.click(*coord)
        time.sleep(0.3)

    # ── 出击 ──────────────────────────────────────────────────────────────

    def start_fight(
        self,
        map: str,
        entrance: Literal['alpha', 'beta'] | None = None,
        skip_check: bool = False,
    ) -> None:
        """选择活动节点并点击出击，等待进入出征准备页面。"""
        if not skip_check:
            if (
                len(map) != 2
                or map[0] not in ('H', 'E')
                or not map[1].isdigit()
                or int(map[1]) not in NODE_POSITIONS
            ):
                raise ValueError(f'无效的地图标识: {map}')
            if entrance not in ('alpha', 'beta', None):
                raise ValueError(f'无效的入口标识: {entrance}')
            difficulty, node_id = map[0], int(map[1])
            self.close_node_overlay()
            self.select_difficulty(difficulty)
            self.select_node(node_id)
            if entrance is not None:
                self.select_entrance(entrance)

        from autowsgr.application.ui.controller.fleet import BattlePreparationPage

        screen = self._ctrl.screenshot()
        detail = self._fight_button_detail(screen)
        if detail is not None:
            coord = detail.center
        else:
            coord = CLICK_FIGHT_BUTTON
            _log.warning('[UI] 活动地图: 未匹配到出击按钮, 回退固定坐标点击')
        _log.debug('[UI] 活动地图: 点击出击')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=coord,
            checker=BattlePreparationPage.check_current_page,
            source=PageName.EVENT_MAP,
            target=PageName.BATTLE_PREP,
        )

    # ── 页面返回 ──────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """返回母港主页，并避免返回按钮因画面滞后被连续点击。

        活动地图可能在战斗回港后保留节点详情浮层，因此先关闭浮层，再点击返回。
        每次返回点击后等待页面稳定，避免下一次点击落到主页左上角的其他控件。
        """
        from autowsgr.application.ui.controller.home.main_page import HomePage
        from autowsgr.common.ui.interaction import NavigationError

        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            screen = self._ctrl.screenshot()
            if HomePage.check_current_page(screen):
                _log.info('[UI] 活动地图 -> 已到达主页面')
                return
            if self._fight_button_detail(screen) is not None:
                _log.info('[UI] 活动地图: 检测到关卡浮层, 点击红色 X 关闭')
                self._ctrl.click(*CLICK_CLOSE_NODE_OVERLAY)
                time.sleep(0.5)
                continue
            self._ctrl.click(*CLICK_BACK)
            settled = time.monotonic() + 3.0
            while time.monotonic() < settled:
                time.sleep(0.3)
            if HomePage.check_current_page(self._ctrl.screenshot()):
                _log.info('[UI] 活动地图 -> 已到达主页面')
                return
        raise NavigationError(
            '活动地图: 返回主页面超时 (浮层/返回点击未能逐层退出)',
            screen=self._ctrl.screenshot(),
        )

    # ── 内部页面识别辅助 ──────────────────────────────────────────────────

    @staticmethod
    def _fight_button_detail(screen: np.ndarray) -> ImageMatchDetail | None:
        """读取节点详情浮层的出击按钮匹配结果。"""
        return ImageChecker.find_any(
            screen,
            _get_fight_button_templates(),
            roi=FIGHT_BUTTON_ROI,
            confidence=0.8,
        )

    @staticmethod
    def _read_difficulty_icon_state(screen: np.ndarray) -> str | None:
        """读取难度切换图标表达的当前难度。"""
        if (
            ImageChecker.find_any(screen, _get_difficulty_hard_templates(), confidence=0.8)
            is not None
        ):
            return 'E'
        if (
            ImageChecker.find_any(screen, _get_difficulty_easy_templates(), confidence=0.8)
            is not None
        ):
            return 'H'
        return None

    def _check_alpha_entrance(self) -> bool:
        """检查当前入口是否为 Alpha。"""
        screen = self._ctrl.screenshot()
        x, y = ENTRANCE_ALPHA_PROBE
        pixel = PixelChecker.get_pixel(screen, x, y)
        return pixel.near(ENTRANCE_ALPHA_COLOR, ENTRANCE_ALPHA_TOLERANCE)


# ── 页面模板加载辅助 ──────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _get_fight_button_templates() -> list[ImageTemplate]:
    """延迟加载节点详情浮层的出击按钮模板。"""
    return event_fight_button_templates()


@lru_cache(maxsize=1)
def _get_event_title_templates() -> list[ImageTemplate]:
    """延迟加载活动地图页面标题模板。"""
    return event_map_title_templates()


@lru_cache(maxsize=1)
def _get_difficulty_hard_templates() -> list[ImageTemplate]:
    """延迟加载简单难度页面显示的困难模式按钮模板。"""
    return event_difficulty_hard_templates()


@lru_cache(maxsize=1)
def _get_difficulty_easy_templates() -> list[ImageTemplate]:
    """延迟加载困难难度页面显示的简单模式按钮模板。"""
    return event_difficulty_easy_templates()
