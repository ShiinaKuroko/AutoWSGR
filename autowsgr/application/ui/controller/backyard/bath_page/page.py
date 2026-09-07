"""模块功能：负责浴室页面识别、修理浮层操作和页面级返回。

上层调用：
- application.ui.navigation.graph.logistics：调用 go_back 完成浴室到后院的页面边动作。
- business.logistics.repair.bath_repair：打开修理浮层、选择舰船并读取修理结果。

下层依赖：
- application.ui.controller.backyard.bath_page.constants：提供页面坐标、颜色和识别参数。
- application.ui.controller.backyard.bath_page.recognition：识别修理卡片并转换修理时长。
- common.ui.interaction：等待浮层出现、关闭或离开页面。
- common.vision：匹配页面模板、浮层模板和按钮颜色。
- common.types：提供页面名称和页面匹配类型。
- common.system.logger：记录页面操作和失败原因。

选择修理是浴室页面上的浮层，浮层打开时仍识别为浴室。页面控制器只负责
浴室内部动作和返回动作，不负责跨页面寻路或修理任务调度。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.backyard.bath_page import constants, recognition
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.vision import Color, ImageChecker, PageMatch, PixelChecker
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('ui')

# 修理结果等待上限属于流程策略，不是屏幕校准值。
BATH_FULL_TIMEOUT = 3.0

_MAX_VISIBLE_CARDS = 5
"""单屏完整可见的修理卡片上限，用于判断是否还需要继续翻页。

当前页卡片数低于此值时，列表已到末尾；即使部分卡片被黑名单排除，也不再
重复滑动查看同一批末尾卡片。
"""


# ── 页面控制器 ──────────────────────────────────────────────────────────────


class BathPage:
    """浴室页面内的 UI 操作控制器。

    选择修理浮层属于浴室页面状态的一部分。浮层打开时仍由
    :meth:`check_current_page` 识别为浴室，具体浮层状态由
    :meth:`check_choose_repair_overlay` 判断。

    Args:
        ctx: 包含 Android 设备控制器的 UI 上下文。
    """

    def __init__(self, ctx: GameContext) -> None:
        """保存页面操作所需的 UI 上下文和设备控制器。"""
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面识别 ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否属于浴室页面，包括选择修理浮层状态。

        1、优先匹配浴室页面基础特征。
        2、基础特征被浮层遮挡时，使用选择修理浮层特征确认仍在浴室页面。
        3、两种特征都未命中时返回不匹配结果。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            页面匹配结果；基础页面或选择修理浮层命中时均视为浴室页面。
        """
        name = PageName.BATH.value
        # 先确认浴室页面的基础特征。
        result = ImageChecker.find_template(screen, Templates.Bath.BATH, confidence=0.85)
        if result is not None:
            return PageMatch(name=name, matched=True, score=result.confidence)
        # 浮层可能遮挡基础特征，使用浮层特征作为同页确认。
        overlay = ImageChecker.find_template(screen, Templates.Bath.CHOOSE_REPAIR, confidence=0.85)
        if overlay is not None:
            return PageMatch(name=name, matched=True, score=overlay.confidence)
        return PageMatch(name=name, matched=False, score=0.0)

    @staticmethod
    def check_choose_repair_overlay(screen: np.ndarray) -> bool:
        """检查截图中的选择修理浮层是否处于打开状态。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            浮层模板命中时为 ``True``，否则为 ``False``。
        """
        return ImageChecker.template_exists(screen, Templates.Bath.CHOOSE_REPAIR, confidence=0.85)

    # ── 选择修理浮层 ──────────────────────────────────────────────────────────

    def open_choose_repair_overlay(self) -> None:
        """打开选择修理浮层，并等待浮层可见。

        如果浮层已经打开则不重复点击；否则点击入口后等待浮层出现。

        Args:
            None.

        Returns:
            None. 浮层未在等待期限内出现时抛出异常。

        Raises:
            NavigationError: 超时未等到选择修理浮层出现。
        """
        from autowsgr.common.ui.interaction import wait_for_page

        _log.info('[UI] 浴室 → 打开选择修理 overlay')
        if not self.check_choose_repair_overlay(self._ctrl.screenshot()):
            self._ctrl.click(*constants.CLICK_CHOOSE_REPAIR)
        wait_for_page(
            self._ctrl,
            BathPage.check_choose_repair_overlay,
            source='浴室',
            target='选择修理 overlay',
        )

    def close_choose_repair_overlay(self) -> None:
        """关闭选择修理浮层，并等待浴室页面恢复为无浮层状态。

        Args:
            None.

        Returns:
            None. 浮层未在等待期限内关闭时抛出异常。

        Raises:
            NavigationError: 超时未等到选择修理浮层关闭。
        """
        from autowsgr.common.ui.interaction import wait_for_page

        _log.info('[UI] 关闭选择修理 overlay')
        self._ctrl.click(*constants.CLICK_CLOSE_OVERLAY)
        # 等待关闭动画完成，并确认页面回到无浮层的浴室状态。
        wait_for_page(
            self._ctrl,
            lambda s: (
                BathPage.check_current_page(s).matched
                and not BathPage.check_choose_repair_overlay(s)
            ),
            source='选择修理 overlay',
            target='浴室',
            timeout=10.0,
        )

    def click_first_repair_ship(self) -> None:
        """点击当前修理列表第一个舰船，并等待游戏回到浴室页面。

        游戏会在选船后自动关闭浮层；若浮层未打开或未能关闭，则报告导航错误。

        Args:
            None.

        Returns:
            None. 点击成功且浮层关闭后停留在浴室页面。

        Raises:
            NavigationError: 浮层未打开或超时未等到浮层关闭。
        """
        from autowsgr.common.ui.interaction import NavigationError

        _log.info('[UI] 选择修理 → 点击第一个舰船')

        # 页面操作必须从已打开的选择修理浮层开始。
        screen = self._ctrl.screenshot()
        if not BathPage.check_choose_repair_overlay(screen):
            raise NavigationError('选择修理 overlay 未打开，无法点击舰船', screen=screen)

        self._ctrl.click(*constants.CLICK_FIRST_REPAIR_SHIP)

        # 选船后游戏会自动关闭浮层，确认仍停在浴室页面。
        if not self._wait_overlay_close():
            raise NavigationError(
                '选择修理 overlay 未关闭，无法确认修理结果', screen=self._ctrl.screenshot()
            )

    def click_repair_all(self) -> None:
        """提交全部修理，并确认选择修理浮层已经关闭。

        如果按钮位置未呈现可点击状态，则退回点击第一个舰船的路径。

        Args:
            None.

        Returns:
            None. 全部修理完成或浮层被主动关闭后返回。

        Raises:
            NavigationError: 浮层未打开，或点击后未能关闭。
        """
        from autowsgr.common.ui.interaction import NavigationError

        screen = self._ctrl.screenshot()
        if not BathPage.check_choose_repair_overlay(screen):
            raise NavigationError('选择修理 overlay 未打开，无法点击全部修理', screen=screen)

        # 先确认“全部修理”按钮仍处于可点击状态。
        btn_color, btn_tol = constants.REPAIR_ALL_BUTTON_COLOR
        px = PixelChecker.get_pixel(screen, *constants.CLICK_REPAIR_ALL)
        if not px.near(Color.from_rgb_tuple(btn_color), btn_tol):
            _log.warning('[UI] 未检测到全部修理按钮，回退到点击第一个舰船')
            self.click_first_repair_ship()
            return

        _log.info('[UI] 选择修理 → 点击全部修理')
        self._ctrl.click(*constants.CLICK_REPAIR_ALL)
        time.sleep(1.0)

        # 等待浮层自行关闭；若仍在且关闭按钮可见，执行页面级收尾。
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            screen = self._ctrl.screenshot()
            if (
                BathPage.check_current_page(screen).matched
                and not BathPage.check_choose_repair_overlay(screen)
            ):
                _log.debug('[UI] 全部修理后 overlay 已自动关闭')
                return

            # 浮层未自行关闭且关闭按钮可见，主动结束浮层状态。
            close_color, close_tol = constants.CLOSE_OVERLAY_BUTTON_COLOR
            close_px = PixelChecker.get_pixel(screen, *constants.CLICK_CLOSE_OVERLAY)
            if close_px.near(Color.from_rgb_tuple(close_color), close_tol):
                _log.debug('[UI] 全部修理后 overlay 仍在，手动关闭')
                self._ctrl.click(*constants.CLICK_CLOSE_OVERLAY)
                # 手动点击也必须确认回到无浮层的浴室页面。
                if not self._wait_overlay_close():
                    raise NavigationError(
                        '全部修理后手动关闭 overlay 失败', screen=self._ctrl.screenshot()
                    )
                return

            time.sleep(0.5)

        raise NavigationError('全部修理后 overlay 未关闭', screen=self._ctrl.screenshot())

    # ── 指定舰船修理 ──────────────────────────────────────────────────────────

    def repair_ship(self, ship_name: str) -> int:
        """在选择修理浮层中查找并修理指定舰船。

        1、从当前页开始识别舰船卡片。
        2、未找到且当前页已填满时继续向后翻页，最多检查 10 页。
        3、点击目标后等待浮层关闭；未关闭时返回修理未完成结果。

        Args:
            ship_name: 要修理的舰船中文名称。

        Returns:
            修理时间（秒）；若点击后浮层未关闭，则返回 ``-1``。

        Raises:
            NavigationError: 选择修理浮层未打开，或舰船未找到。
        """
        from autowsgr.common.ui.interaction import NavigationError

        screen = self._ctrl.screenshot()
        if not BathPage.check_choose_repair_overlay(screen):
            raise NavigationError('选择修理 overlay 未打开，无法修理指定舰船', screen=screen)

        # 最多检查 10 页，避免在不循环的列表中无限查找。
        for _attempt in range(10):
            ships = self.recognize_repair_ships()
            for ship in ships:
                if ship.name == ship_name:
                    _log.info('[UI] 选择修理: 找到 {} (耗时 {})，点击', ship_name, ship.repair_time)
                    repair_secs = recognition.convert_repair_time_to_seconds(ship.repair_time)
                    self._ctrl.click(*ship.position)

                    # 选船后浮层未关闭，按当前业务契约视为浴场无法接收修理。
                    if self._wait_overlay_close():
                        _log.info('[UI] 修理成功: {} ({}s)', ship_name, repair_secs)
                        return repair_secs

                    _log.warning('[UI] 浴场已满, 无法修理 {}', ship_name)
                    return -1
            if len(ships) < _MAX_VISIBLE_CARDS:
                # 当前页未填满，说明已到列表末尾，不再重复滑动。
                _log.debug(
                    '[UI] 选择修理: 本页仅 {} 张卡片 (<{}), 已到列表末尾，停止翻页',
                    len(ships),
                    _MAX_VISIBLE_CARDS,
                )
                break
            # 当前页没有目标且仍可能有后续卡片，继续查看下一页。
            self._swipe_left()

        raise NavigationError(
            f'选择修理 overlay 中未找到舰船 "{ship_name}"',
            screen=self._ctrl.screenshot(),
        )

    def repair_longest(self, blacklist: set[str] | None = None) -> tuple[str, int]:
        """选择并修理当前列表中耗时最长的非黑名单舰船。

        1、按页识别修理卡片，在第一个包含候选舰船的页面内选择耗时最长者。
        2、当前页未填满时视为列表末尾；最多检查 10 页。
        3、点击候选后等待浮层关闭，再返回舰船名和修理时长。

        Args:
            blacklist: 不修理的舰船中文名称集合；命中后跳过对应舰船。

        Returns:
            成功返回 ``(舰船名, 修理秒数)``；无可修候选返回 ``('', -1)``；
            浴场已满返回 ``('', -2)``。
        """
        blocked = blacklist or set()
        target: recognition.RepairShipInfo | None = None
        for _ in range(10):
            ships = self.recognize_repair_ships()
            candidates = [s for s in ships if s.name and s.name not in blocked]
            if candidates:
                target = max(
                    candidates,
                    key=lambda s: recognition.convert_repair_time_to_seconds(s.repair_time),
                )
                break
            if len(ships) < _MAX_VISIBLE_CARDS:
                # 当前页未填满，说明已到列表末尾，不再重复滑动。
                _log.debug(
                    '[UI] 选择修理: 本页仅 {} 张卡片 (<{}), 已到列表末尾，停止翻页',
                    len(ships),
                    _MAX_VISIBLE_CARDS,
                )
                break
            self._swipe_left()

        if target is None:
            _log.info('[UI] 选择修理: 无可修理舰船 (或均被黑名单排除)')
            return '', -1

        _log.info(
            '[UI] 选择修理 → 修理最长: {} ({})',
            target.name,
            target.repair_time,
        )
        self._ctrl.click(*target.position)
        if self._wait_overlay_close():
            return target.name, recognition.convert_repair_time_to_seconds(target.repair_time)
        _log.warning('[UI] 浴场已满, 修理 {} 失败', target.name)
        return '', -2

    # ── 修理卡片识别 ──────────────────────────────────────────────────────────

    def recognize_repair_ships(self) -> list[recognition.RepairShipInfo]:
        """识别选择修理浮层中当前可见的待修理舰船。

        Args:
            None.

        Returns:
            当前可见待修理舰船列表；列表按卡片从左到右排列。
        """
        from autowsgr.common.vision import OCREngine

        screen = self._ctrl.screenshot()
        ocr = OCREngine.create()
        return recognition.recognize_repair_cards(screen, ocr)

    # ── 浮层操作辅助 ──────────────────────────────────────────────────────────

    def _swipe_left(self) -> None:
        """向左滑动修理列表，为后续卡片识别让出可见区域。

        Args:
            None.

        Returns:
            None. 滑动完成并等待页面稳定后返回。
        """
        _log.debug('[UI] 选择修理 overlay: 向左滑动')
        self._ctrl.swipe(
            *constants.SWIPE_START,
            *constants.SWIPE_END,
            duration=constants.SWIPE_DURATION,
        )
        time.sleep(constants.SWIPE_DELAY)

    def _wait_overlay_close(self) -> bool:
        """最多等待 ``BATH_FULL_TIMEOUT`` 秒确认修理浮层关闭。

        Args:
            None.

        Returns:
            ``True`` 表示浮层已关闭；``False`` 表示超时后浮层仍打开，
            调用方据此区分修理成功和浴场无法接收修理。
        """
        deadline = time.monotonic() + BATH_FULL_TIMEOUT
        while time.monotonic() < deadline:
            screen = self._ctrl.screenshot()
            if BathPage.check_current_page(
                screen
            ).matched and not BathPage.check_choose_repair_overlay(screen):
                return True
            time.sleep(0.5)
        return False

    # ── 页面级返回 ────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """从浴室页面执行页面级回退。

        1、选择修理浮层打开时，先关闭浮层并停留在浴室。
        2、没有浮层时，点击返回按钮并等待离开浴室，回到后院或出征准备。

        Args:
            None.

        Returns:
            None. 浮层打开时只关闭浮层；否则返回后院或出征准备页面。

        Raises:
            NavigationError: 超时未完成回退。
        """
        from autowsgr.common.ui.interaction import wait_leave_page

        screen = self._ctrl.screenshot()
        if BathPage.check_choose_repair_overlay(screen):
            # 浮层打开时先回到浴室页面本体，不跨页面返回。
            self.close_choose_repair_overlay()
            return

        _log.info('[UI] 浴室 → 返回')
        self._ctrl.click(*constants.CLICK_BACK)
        wait_leave_page(
            self._ctrl,
            BathPage.check_current_page,
            source='浴室',
            target='后院/出征准备',
        )
