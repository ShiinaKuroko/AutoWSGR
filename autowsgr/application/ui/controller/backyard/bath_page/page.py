"""模块功能：编排浴室页面流程，并提供页面级导航入口。

上层调用：
- application.ui.navigation.graph.logistics：调用 `go_back` 完成浴室到后院的页面边动作。
- business.logistics.repair.bath_repair：调用完整的修理流程入口。

下层依赖：
- application.ui.controller.backyard.bath_page.recognition：提供页面事实。
- application.ui.controller.backyard.bath_page.operations：提供页面原子操作。
- common.device.interaction：确认页面级返回终态。

边界：
本模块只提供页面事实、页面级导航和稳定的修理流程入口，不实现修理分支、分页选择
或终态判断。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.backyard.bath_page import (
    constants,
    operations,
    recognition,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.interaction import NavigationError, wait_for_page, wait_leave_page


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.application.ui.navigation.types import PageMatch


_log = get_logger('ui.bath_page')

_OVERLAY_CLOSE_TIMEOUT = 10.0  # 浮层关闭终态的最长等待时间（秒）。
_REPAIR_RESULT_TIMEOUT = 3.0  # 单艘舰船修理结果的最长确认时间（秒）。
_REPAIR_ALL_SETTLE_DELAY = 1.0  # 全部修理点击后的页面稳定等待时间（秒）。
_REPAIR_ALL_TIMEOUT = 10.0  # 全部修理后的浮层终态确认上限（秒）。
_REPAIR_ALL_POLL_INTERVAL = 0.5  # 全部修理终态轮询间隔（秒）。
_MAX_REPAIR_PAGES = 10  # 单次修理流程最多扫描的列表页数。
_MAX_VISIBLE_REPAIR_CARDS = 5  # 单页完整可见卡片数，用于判断列表是否到末尾。


RepairResult = None | int | tuple[str, int]
"""浴室修理流程的统一结果。"""


class BathPage:
    """浴室页面流程编排和上层调用入口。"""

    def __init__(self, ctx: UIContext) -> None:
        """保存调用方注入的上下文和设备控制器。

        Args:
            ctx: 提供设备控制器和共享 OCR 引擎的 UI 上下文。
        """
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面事实入口 ──────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否属于浴室页面。

        Args:
            screen: 浴室页面 RGB 截图。

        Returns:
            页面匹配结果；基础页面或选择修理浮层命中时均视为浴室页面。
        """
        return recognition.check_current_page(screen)

    # ── 修理流程入口 ──────────────────────────────────────────────────────────

    # 按页面业务契约集中保留打开浮层、分支选择和终态确认的执行顺序。
    def repair(  # noqa: C901, PLR0911, PLR0912
        self,
        *,
        repair_all: bool,
        ship_name: str | None = None,
        blacklist: set[str] | None = None,
    ) -> RepairResult:
        """打开修理浮层，并根据入参完成全部或手动修理。

        Args:
            repair_all: 为 True 时提交全部修理；为 False 时执行手动选择流程。
            ship_name: 手动流程指定的舰船名称；为空时选择耗时最长的候选。
            blacklist: 未指定舰船时排除的舰船名称集合。

        Returns:
            全部修理返回 None；指定舰船返回修理秒数；自动选择候选时返回舰船名和秒数。

        Raises:
            NavigationError: 无法打开浮层或未能确认修理终态。
            LookupError: 指定舰船不在修理列表中。
            ValueError: 修理参数组合不合法。
        """
        if repair_all and (ship_name is not None or blacklist is not None):
            raise ValueError('全部修理不能同时指定舰船或黑名单')
        if not repair_all and ship_name is not None and blacklist is not None:
            raise ValueError('指定舰船修理不能同时指定黑名单')

        ctrl = self._ctrl

        # 1. 点击右上角入口并确认选择修理浮层出现。
        if not recognition.check_choose_repair_overlay(ctrl.screenshot()):
            operations.click_choose_repair(ctrl)
        wait_for_page(
            ctrl,
            recognition.check_choose_repair_overlay,
            source='浴室',
            target='选择修理浮层',
        )
        _log.info('[UI] 浴室 → 打开选择修理浮层：结果=成功')

        # 2. 全部修理分支。
        if repair_all:
            screen = ctrl.screenshot()
            if not recognition.check_repair_all_available(screen):
                operations.click_repair_card(ctrl, constants.CLICK_FIRST_REPAIR_SHIP)
                if not operations.wait_overlay_closed(
                    ctrl,
                    page_checker=lambda frame: recognition.check_current_page(frame).matched,
                    overlay_checker=recognition.check_choose_repair_overlay,
                    timeout=_REPAIR_RESULT_TIMEOUT,
                ):
                    raise NavigationError(
                        '选择修理浮层未关闭，无法确认修理结果',
                        screen=ctrl.screenshot(),
                    )
                _log.info('[UI] 选择修理浮层 → 修理首艘舰船：结果=成功')
                return None

            _log.info('[UI] 选择修理浮层 → 点击全部修理：状态=开始')
            operations.click_repair_all(ctrl)
            time.sleep(_REPAIR_ALL_SETTLE_DELAY)
            deadline = time.monotonic() + _REPAIR_ALL_TIMEOUT
            while time.monotonic() < deadline:
                screen = ctrl.screenshot()
                if recognition.check_current_page(
                    screen
                ).matched and not recognition.check_choose_repair_overlay(screen):
                    _log.info('[UI] 选择修理浮层 → 全部修理：结果=成功')
                    return None

                if recognition.check_close_overlay_available(screen):
                    _log.warning(
                        '[UI] 选择修理浮层 → 手动收尾：原因={!r}，下一步={!r}',
                        '浮层仍然打开',
                        '关闭浮层',
                    )
                    operations.click_close_overlay(ctrl)
                    if not operations.wait_overlay_closed(
                        ctrl,
                        page_checker=lambda frame: recognition.check_current_page(frame).matched,
                        overlay_checker=recognition.check_choose_repair_overlay,
                        timeout=_REPAIR_RESULT_TIMEOUT,
                    ):
                        raise NavigationError(
                            '全部修理后手动关闭浮层失败',
                            screen=ctrl.screenshot(),
                        )
                    _log.info('[UI] 选择修理浮层 → 全部修理：结果=成功')
                    return None

                time.sleep(_REPAIR_ALL_POLL_INTERVAL)

            raise NavigationError('全部修理后浮层未关闭', screen=ctrl.screenshot())

        # 3. 手动分支：指定舰船，或从候选中选择修理时间最长者。
        blocked = set(blacklist or ())
        for attempt in range(_MAX_REPAIR_PAGES):
            if self._ctx.ocr is None:
                raise RuntimeError('浴室修理需要 OCR 引擎')
            ships = recognition.recognize_repair_cards(ctrl.screenshot(), self._ctx.ocr)
            target = next((ship for ship in ships if ship.name == ship_name), None)
            if ship_name is None:
                candidates = [ship for ship in ships if ship.name and ship.name not in blocked]
                target = (
                    max(
                        candidates,
                        key=lambda ship: recognition.convert_repair_time_to_seconds(
                            ship.repair_time
                        ),
                    )
                    if candidates
                    else None
                )

            if target is not None:
                repair_seconds = recognition.convert_repair_time_to_seconds(target.repair_time)
                _log.info(
                    '[UI] 选择修理浮层 → 选择舰船：舰船={!r}，修理时间={!r}，状态=开始',
                    target.name,
                    target.repair_time,
                )
                operations.click_repair_card(ctrl, target.position)
                closed = operations.wait_overlay_closed(
                    ctrl,
                    page_checker=lambda frame: recognition.check_current_page(frame).matched,
                    overlay_checker=recognition.check_choose_repair_overlay,
                    timeout=_REPAIR_RESULT_TIMEOUT,
                )
                if closed:
                    _log.info(
                        '[UI] 选择修理浮层 → 修理成功：舰船={!r}，修理秒数={}',
                        target.name,
                        repair_seconds,
                    )
                    if ship_name is None:
                        return target.name, repair_seconds
                    return repair_seconds

                _log.warning(
                    '[UI] 选择修理浮层 → 修理失败：舰船={!r}，原因={!r}，结果=失败',
                    target.name,
                    '浴室已满',
                )
                if ship_name is None:
                    return '', -2
                return -1

            if len(ships) < _MAX_VISIBLE_REPAIR_CARDS:
                break
            if attempt == _MAX_REPAIR_PAGES - 1:
                break
            operations.swipe_repair_list(ctrl)

        if ship_name is not None:
            raise LookupError(f'选择修理浮层中未找到舰船 "{ship_name}"')
        _log.info('[UI] 选择修理浮层 → 无可修舰船：结果=未找到')
        return '', -1

    # ── 页面级导航 ────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """从浴室页面返回调用方页面；浮层打开时先关闭浮层。

        Raises:
            NavigationError: 点击返回后超时仍未离开浴室页面。
        """
        screen = self._ctrl.screenshot()
        # 浮层属于浴室页面状态，先关闭浮层，不直接触发跨页面返回。
        if recognition.check_choose_repair_overlay(screen):
            operations.click_close_overlay(self._ctrl)
            wait_for_page(
                self._ctrl,
                lambda frame: (
                    recognition.check_current_page(frame).matched
                    and not recognition.check_choose_repair_overlay(frame)
                ),
                source='选择修理浮层',
                target='浴室',
                timeout=_OVERLAY_CLOSE_TIMEOUT,
            )
            _log.info('[UI] 选择修理浮层 → 关闭：结果=成功')
            return

        # 页面级导航由本页完成点击，并交给导航基础设施确认离开终态。
        _log.info('[UI] 浴室 → 返回：状态=开始')
        operations.click_back(self._ctrl)
        wait_leave_page(
            self._ctrl,
            self.check_current_page,
            source='浴室',
            target='后院/出征准备',
        )
        _log.info('[UI] 浴室 → 返回：结果=成功')


__all__ = ['BathPage']
