"""决战总览页 UI 控制器。

对应游戏 **决战地图总览页** — 从地图页「决战」面板进入。

使用方式::

    from autowsgr.application.ui.controller.decisive import DecisiveBattlePage

    page = DecisiveBattlePage(ctrl, ocr=ocr)
    stage = page.recognize_stage(screen, chapter=6)
    page.enter_map()
    page.go_back()
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from autowsgr.common.calibration.decisive import (
    CHAPTER_NUM_AREA,
    CLICK_BACK,
    CLICK_BUY_CONFIRM,
    CLICK_BUY_RESOURCE,
    CLICK_BUY_TICKET_OPEN,
    CLICK_ENTER_MAP,
    CLICK_NEXT_CHAPTER,
    CLICK_PREV_CHAPTER,
    CLICK_RESET_CHAPTER,
    STAGE_CHECK_COLOR as _STAGE_CHECK_COLOR,
    STAGE_CHECK_POINTS as _STAGE_CHECK_POINTS,
    STAGE_CHECK_TOLERANCE as _STAGE_CHECK_TOLERANCE,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import DecisiveEntryStatus, PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page, confirm_operation
from autowsgr.common.vision import ImageChecker, OCREngine, PageMatch, PixelChecker
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('ui.decisive')

# ═══════════════════════════════════════════════════════════════════════════════
# 页面识别签名
# ═══════════════════════════════════════════════════════════════════════════════



# ═══════════════════════════════════════════════════════════════════════════════
# 坐标常量 (相对坐标 0.0-1.0, 参考分辨率 960x540)
# ═══════════════════════════════════════════════════════════════════════════════







# ── 磁盘购买 ──




# ── 其他常量 ──

_CHAPTER_SWITCH_DELAY: float = 0.8
"""章节切换动画延迟 (秒)。"""

_CHAPTER_NAV_MAX_ATTEMPTS: int = 8
"""章节导航最大尝试次数。"""

MAX_CHAPTER: int = 6
MIN_CHAPTER: int = 1

# ── recognize_stage 检测点 ──





# ═══════════════════════════════════════════════════════════════════════════════
# 页面控制器
# ═══════════════════════════════════════════════════════════════════════════════


class DecisiveBattlePage:
    """决战总览页控制器。

    **状态查询** 为 ``staticmethod``，只需截图即可调用。
    **操作动作** 为实例方法，通过注入的控制器执行。

    Parameters
    ----------
    ctrl:
        Android 设备控制器实例。
    ocr:
        OCR 引擎实例 (可选，章节导航时需要)。
    """

    def __init__(
        self,
        ctx: GameContext,
        ocr: OCREngine | None = None,
    ) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl
        self._ocr = ocr or ctx.ocr

    # ── 页面识别 ──────────────────────────────────────────────────────────

    @staticmethod
    def is_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否为决战总览页。

        用总览页独有的入口状态图标 (4 种: 无法出击 / 挑战中 / 已刷新 / 可重置,
        即 classic ``decisive_battle_image[3:7]``) 匹配, 命中任一即认定在总览页。
        这些图标只在总览页出现 — 全截图交叉验证其他页置信度 < 0.7, 不误命中。
        阈值 0.8 与 :meth:`detect_entry_status` 一致 (入口状态图标本身较小,
        置信度约 0.8+)。旧像素签名 ``PAGE_SIGNATURE`` (4 个深色背景点, 曾在
        深色活动主题页误命中) 保留备查, 不再参与判定。
        """
        result = ImageChecker.find_any(
            screen, Templates.Decisive.entry_status_templates(), confidence=0.8
        )
        name = PageName.DECISIVE_BATTLE.value
        if result is None:
            return PageMatch(name=name, matched=False, score=0.0)
        return PageMatch(name=name, matched=True, score=result.confidence)

    # ── 小关进度识别 ──────────────────────────────────────────────────────

    @staticmethod
    def recognize_stage(screen: np.ndarray, chapter: int) -> int:
        """识别当前决战章节的小关进度 (0-3)。

        检查每个小关位置像素颜色，白色 (250,244,253) 为已通过。
        返回当前正在进行的小关编号; 3 表示全部通过。
        """
        check_points = _STAGE_CHECK_POINTS.get(chapter)
        if check_points is None:
            _log.warning('[决战] 决战 recognize_stage: 未知章节 {}', chapter)
            return 0

        for i, (rx, ry) in enumerate(check_points):
            if not PixelChecker.check_pixel(
                screen,
                rx,
                ry,
                _STAGE_CHECK_COLOR,
                _STAGE_CHECK_TOLERANCE,
            ):
                _log.info('[决战] 识别决战地图参数, 第 {} 小节正在进行', i)
                return i

        _log.info('[决战] 识别决战地图参数, 第 3 小节正在进行')
        return 3

    def detect_stage(self, screen: np.ndarray, chapter: int) -> int:
        """识别小节号（统一调用 recognize_stage）。"""
        return self.recognize_stage(screen, chapter)

    # ── 导航 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击左上角 ◁，直接返回主页面 (跨级)。"""
        from autowsgr.application.ui.controller.home import HomePage

        _log.info('[决战] 决战页面 ◁ → 主页面')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=CLICK_BACK,
            checker=HomePage.check_current_page,
            source=PageName.DECISIVE_BATTLE,
            target=PageName.HOME,
        )

    def click_enter_map(self) -> None:
        """从决战总览页进入当前章节的决战地图页。"""
        _log.info('[决战] 决战总览 → 进入地图')
        self._ctrl.click(*CLICK_ENTER_MAP)

    # ── 章节 OCR ──────────────────────────────────────────────────────────

    def _read_chapter(self, screen: np.ndarray | None = None) -> int | None:
        """通过 OCR 读取当前章节编号 (Ex-N → N)。

        使用字符白名单 ``0123456789Ex-`` 提升准确率，
        避免将数字误识别为字母 (如 ``6`` → ``G``)。
        """
        if self._ocr is None:
            return None
        if screen is None:
            screen = self._ctrl.screenshot()

        x1, y1, x2, y2 = CHAPTER_NUM_AREA
        cropped = PixelChecker.crop(screen, x1, y1, x2, y2)
        result = self._ocr.recognize_single(cropped, allowlist='0123456789Ex-')
        if not result.text:
            _log.debug('[决战] 决战章节 OCR 无结果')
            return None

        m = re.search(r'(\d)', result.text[::-1])
        if m:
            chapter = int(m.group(1))
            _log.debug("[决战] 决战章节 OCR: '{}' → Ex-{}", result.text, chapter)
            return chapter

        _log.debug("[决战] 决战章节 OCR 解析失败: '{}'", result.text)
        return None

    # ── 章节导航 ──────────────────────────────────────────────────────────

    def go_prev_chapter(self) -> None:
        """点击 ◁ 切换到前一章节。"""
        _log.info('[决战] 决战页面 → 前一章节 ◁')
        self._ctrl.click(*CLICK_PREV_CHAPTER)
        time.sleep(_CHAPTER_SWITCH_DELAY)

    def go_next_chapter(self) -> None:
        """点击 ▷ 切换到后一章节。"""
        _log.info('[决战] 决战页面 → 后一章节 ▷')
        self._ctrl.click(*CLICK_NEXT_CHAPTER)
        time.sleep(_CHAPTER_SWITCH_DELAY)

    def navigate_to_chapter(self, target: int) -> None:
        """导航到指定决战章节。

        通过 OCR 读取当前章节编号，反复点击 ◁/▷ 直到到达目标。

        Parameters
        ----------
        target:
            目标章节编号 (MIN_CHAPTER - MAX_CHAPTER)。

        Raises
        ------
        ValueError
            章节号超出范围。
        RuntimeError
            需要 OCR 引擎但未传入。
        NavigationError
            超过最大尝试次数仍未到达。
        """
        from autowsgr.common.ui.interaction import NavigationError

        if not MIN_CHAPTER <= target <= MAX_CHAPTER:
            raise ValueError(f'决战章节编号必须为 {MIN_CHAPTER}-{MAX_CHAPTER}，收到: {target}')
        if self._ocr is None:
            raise RuntimeError('navigate_to_chapter 需要 OCR 引擎')

        for attempt in range(_CHAPTER_NAV_MAX_ATTEMPTS):
            current = self._read_chapter()
            if current is None:
                _log.warning(
                    '[决战] 决战章节导航: OCR 识别失败 (第 {} 次尝试)',
                    attempt + 1,
                )
                time.sleep(_CHAPTER_SWITCH_DELAY)
                continue

            if current == target:
                _log.info('[决战] 决战章节导航: 已到达 Ex-{}', target)
                return

            if current > target:
                self.go_prev_chapter()
            else:
                self.go_next_chapter()

        raise NavigationError(
            f'决战章节导航失败: 超过 {_CHAPTER_NAV_MAX_ATTEMPTS} 次尝试, 目标 Ex-{target}',
            screen=self._ctrl.screenshot(),
        )

    # ── 磁盘购买 ─────────────────────────────────────────────────────────

    def buy_ticket(
        self,
        use: str = 'steel',
        times: int = 3,
    ) -> None:
        """购买决战磁盘 (入场券)。

        Parameters
        ----------
        use:
            资源类型: ``"oil"``/``"ammo"``/``"steel"``/``"aluminum"``。
        times:
            单次资源点击次数。

        Raises
        ------
        ValueError
            资源类型无效。
        """
        if use not in CLICK_BUY_RESOURCE:
            raise ValueError(f'资源类型必须为 oil/ammo/steel/aluminum，收到: {use}')

        _log.info('[决战] 决战页面 → 购买磁盘 (资源: {}, 次数: {})', use, times)
        self._ctrl.click(*CLICK_BUY_TICKET_OPEN)
        time.sleep(1.5)

        resource_pos = CLICK_BUY_RESOURCE[use]
        for _ in range(times):
            self._ctrl.click(*resource_pos)
            time.sleep(1.0)

        self._ctrl.click(*CLICK_BUY_CONFIRM)
        time.sleep(1.0)
        _log.info('[决战] 决战磁盘购买完成')

    # ── 入口状态检测 ─────────────────────────────────────────────────────

    def detect_entry_status(
        self,
        *,
        timeout: float = 10.0,
        interval: float = 0.3,
        confidence: float = 0.8,
    ) -> DecisiveEntryStatus:
        """检测当前决战总览页的入口状态。

        通过图像模板匹配识别 4 种入口状态:
        ``CANT_FIGHT`` / ``CHALLENGING`` / ``REFRESHED`` / ``REFRESH``。

        对应 legacy ``detect('enter_map')`` — 使用
        ``decisive_battle_image[3:7]`` 的 ``wait_images``。

        Parameters
        ----------
        timeout:
            最大等待时间 (秒)。
        interval:
            截图检测间隔 (秒)。
        confidence:
            模板匹配置信度阈值。

        Returns
        -------
        DecisiveEntryStatus
            检测到的入口状态枚举值。

        Raises
        ------
        TimeoutError
            超时仍未匹配到任何入口状态。
        """
        from autowsgr.common.vision.resources import Templates

        templates = Templates.Decisive.entry_status_templates()
        statuses = list(DecisiveEntryStatus)

        deadline = time.monotonic() + timeout
        while True:
            screen = self._ctrl.screenshot()
            detail = ImageChecker.find_any(
                screen,
                templates,
                confidence=confidence,
            )
            if detail is not None:
                idx = next(i for i, t in enumerate(templates) if t.name == detail.template_name)
                status = statuses[idx]
                _log.info('[决战] 决战入口状态: {}', status.value)
                return status

            if time.monotonic() >= deadline:
                raise TimeoutError(f'检测决战入口状态超时 ({timeout}s): 未匹配到任何状态模板')
            time.sleep(interval)

    # ── 章节重置 ─────────────────────────────────────────────────────────

    def reset_chapter(self) -> bool:
        """使用磁盘重置当前章节。

        在决战总览页点击"重置关卡"按钮并确认操作。
        完全对应 legacy ``DecisiveBattle.reset_chapter`` 中的 UI 操作。

        .. note::

            调用前需确保已在决战总览页且已导航到目标章节。
            船坞已满处理由调用方负责。
        """
        _log.info('[决战] 决战页面 → 重置关卡')
        self._ctrl.click(*CLICK_RESET_CHAPTER)
        time.sleep(1.0)
        screen = self._ctrl.screenshot()
        if ImageChecker.template_exists(
            screen,
            Templates.Build.SHIP_FULL_DEPOT,
            confidence=0.8,
        ):
            _log.warning('[决战] 重置关卡时检测到船坞已满')
            return False
        confirm_operation(self._ctrl, must_confirm=True, timeout=5.0)
        time.sleep(1.0)  # 防止后续 stage 识别出问题
        _log.info('[决战] 决战关卡重置完成')
        return True
