"""模块功能：读取远征槽位状态并收取已完成的远征。

上层调用：
- business.logistics.expedition：检查通知并执行远征收取。
- testing.ui：验证远征槽位和结算操作。

下层依赖：
- application.ui.controller.operations.sortie_page.battle_page.base：提供地图页面状态和跳过动画动作。
- application.ui.controller.operations.sortie_page.expedition_page.constants：提供远征状态颜色和槽位坐标。
- common.ui.interaction、common.vision：确认结算和页面返回。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.battle_page.base import BaseMapPage
from autowsgr.application.ui.controller.operations.sortie_page.expedition_page import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import confirm_operation, wait_for_page
from autowsgr.common.vision import Color, ImageChecker, PixelChecker
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np


_log = get_logger('ui')
_READY_COLOR = Color.from_rgb_tuple(constants.READY_COLOR)


class ExpeditionPanelMixin(BaseMapPage):
    """Mixin: 远征面板操作 — 远征收取。"""

    # ── 查询 ─────────────────────────────────────────────────────────────

    @staticmethod
    def read_ready_expedition_slot(screen: np.ndarray) -> int | None:
        """读取 4 个远征槽位，返回第一个已完成槽位。

        Args:
            screen: 当前地图页面截图。

        Returns:
            已完成槽位索引（0-3）；没有可收取远征时返回 ``None``。
        """
        for i, (px, py) in enumerate(constants.SLOT_PROBES):
            actual = PixelChecker.get_pixel(screen, px, py)
            if actual.near(_READY_COLOR, constants.SLOT_TOLERANCE):
                _log.debug(
                    '[UI] 远征槽位 {} 就绪: 实际颜色 {} ≈ 黄色',
                    i + 1,
                    actual.as_rgb_tuple(),
                )
                return i
        return None

    # ── 操作 ─────────────────────────────────────────────────────────────

    def collect_expedition(self) -> int:
        """在远征面板收取已完成的远征。

        Returns:
            本次收取的远征数量。

        Raises:
            NavigationError: 远征通知仍在但 10 秒内无法检测到就绪槽位。
        """
        collected = 0
        for _ in range(8):
            # ── 检测就绪槽位 (含等待逻辑) ──
            screen = self._ctrl.screenshot()
            slot_idx = self.read_ready_expedition_slot(screen)
            if slot_idx is None:
                # 无黄色槽位 — 检查上方探测点是否仍报告有远征
                if not self.check_expedition_notification(screen):
                    _log.debug('[UI] 远征收取: 无就绪槽位且无通知，结束')
                    break

                # 上方探测点仍亮 — 等待槽位刷新 (最多 10s)
                _log.debug('[UI] 远征收取: 通知仍在，等待槽位刷新…')
                deadline = time.monotonic() + 10.0
                while time.monotonic() < deadline:
                    time.sleep(0.1)
                    screen = self._ctrl.screenshot()
                    slot_idx = self.read_ready_expedition_slot(screen)
                    if slot_idx is not None:
                        break
                    if not self.check_expedition_notification(screen):
                        _log.debug('[UI] 远征收取: 通知消失，结束')
                        break
                else:
                    from autowsgr.common.ui.interaction import NavigationError

                    raise NavigationError(
                        '远征收取超时: 通知仍在但 10s 内未检测到就绪槽位',
                        screen=screen,
                    )

                if slot_idx is None:
                    break

            slot_pos = constants.SLOT_PROBES[slot_idx]
            _log.info(
                '[UI] 远征收取: 点击槽位 {} ({:.4f}, {:.4f})',
                slot_idx + 1,
                *slot_pos,
            )

            # 1. 点击就绪槽位
            self._ctrl.click(*slot_pos)
            time.sleep(1.0)

            # 2. 等待远征结果画面
            _result_templates = [Templates.Symbol.CLICK_TO_CONTINUE]
            _wait_deadline = time.monotonic() + 5.0
            while time.monotonic() < _wait_deadline:
                screen = self._ctrl.screenshot()
                if ImageChecker.template_exists(screen, _result_templates):
                    break
            time.sleep(0.25)

            # 3. 点击屏幕右侧跳过动画
            self.click_expedition_skip()
            time.sleep(1.0)

            # 4. 确认弹窗
            confirm_operation(
                self._ctrl,
                must_confirm=True,
                delay=0.5,
                confidence=0.9,
                timeout=5.0,
            )

            # 5. 等待回到地图页面
            wait_for_page(
                self._ctrl,
                checker=self.check_current_page,
                source='远征收取',
                target=PageName.MAP,
            )

            collected += 1

        _log.info('[UI] 远征收取: {} 支', collected)
        return collected
