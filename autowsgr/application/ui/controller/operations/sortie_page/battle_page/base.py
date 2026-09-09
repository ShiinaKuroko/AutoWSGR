"""模块功能：提供战斗地图页面的共享状态读取、面板切换和母港回退操作。

上层调用：
- application.ui.controller.operations.sortie_page.battle_page.page：组合完整地图页面控制器。
- application.ui.controller.operations.sortie_page：复用地图页面状态和面板动作。
- application.ui.navigation、business：执行地图回退、面板切换和远征状态读取。

下层依赖：
- application.ui.controller.operations.sortie_page.battle_page.constants：提供地图页面私有校准。
- application.ui.controller.operations.sortie_page.battle_page.data：提供面板和章节数据类型。
- application.ui.controller.operations.sortie_page.battle_page.recognition：提供地图标题和章节槽位 OCR。
- common.ui.interaction、common.vision：等待页面并检查模板、像素和 OCR 结果。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.battle_page.constants import (
    CLICK_BACK,
    CLICK_EXPEDITION_SKIP,
    EXPEDITION_NOTIF_COLOR,
    EXPEDITION_NOTIF_PROBE,
    EXPEDITION_TOLERANCE,
    PANEL_POSITIONS,
    SIDEBAR_SCAN_STEP,
    SIDEBAR_SCAN_X,
    SIDEBAR_SCAN_Y_RANGE,
)
from autowsgr.application.ui.controller.operations.sortie_page.battle_page.data import (
    PANEL_LIST,
    PANEL_TO_INDEX,
    ChapterSlot,
    MapPanel,
)
from autowsgr.application.ui.controller.operations.sortie_page.battle_page.recognition import (
    MapIdentity,
    recognize_chapter_slots,
    recognize_map,
)
from autowsgr.application.ui.controller.shared.top_tabs import (
    TabbedPageType,
    check_tabbed_page,
    get_active_tab_index,
    make_tab_checker,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import NavigationError, click_and_wait_for_page
from autowsgr.common.vision import OCREngine, PageMatch, PixelChecker


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('ui')


class BaseMapPage:
    """地图页面基类。

    声明所有面板 Mixin 需要的共享依赖与公共查询 / 导航方法。

    Parameters
    ----------
    ctx:
        由调用方注入的运行时 UI 上下文。
    """

    _PANEL_SWITCH_MAX_RETRIES = 3
    """面板切换失败时的最大重试次数。"""

    _PANEL_SWITCH_RETRY_DELAY = 1.0
    """面板切换重试前的等待时间。"""

    def __init__(
        self,
        ctx: GameContext,
    ) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl
        self._ocr = ctx.ocr

    # ── 页面检查 ──────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否为地图页面 (返回带覆盖度分数的 PageMatch)。"""
        return check_tabbed_page(screen, TabbedPageType.MAP)

    # ── 远征通知检查 ──────────────────────────────────────────────────────

    @staticmethod
    def check_expedition_notification(screen: np.ndarray) -> bool:
        """检测是否有远征完成通知。"""
        x, y = EXPEDITION_NOTIF_PROBE
        return PixelChecker.get_pixel(screen, x, y).near(
            EXPEDITION_NOTIF_COLOR, EXPEDITION_TOLERANCE
        )

    # ── 面板状态读取 ──────────────────────────────────────────────────────

    @staticmethod
    def read_active_panel(screen: np.ndarray) -> MapPanel | None:
        """获取当前激活的面板标签。"""
        idx = get_active_tab_index(screen)
        if idx is None or idx >= len(PANEL_LIST):
            return None
        return PANEL_LIST[idx]

    # ── 章节侧栏状态读取 ──────────────────────────────────────────────────

    @staticmethod
    def read_selected_chapter_y(screen: np.ndarray) -> float | None:  # noqa: PLR0912
        """扫描侧边栏, 定位选中章节高亮条的 y 坐标。

        单级算法: 自适应阈值 + 连续段 (中心加权)。
          - 阈值 = max(峰值亮度x0.70, 均值+40), 放宽以兼容不同高亮主题;
          - 邻接高亮点合并为「段」, 取最长段 (≥2 step 合格) 的亮度加权中心;
          - 段覆盖 3%~60% 视为有效; 超出该范围直接返回 None。
          - **不再使用 Top-K 均值降级**: 之前 12% 亮点加权均值实际等价
            于「侧边栏所有文字像素亮度中心」≈ 屏幕 0.45~0.5 固定区域,
            与真实选中章高亮位置完全无关, 导致 target_y 恒定跳错。
        """
        y_min, y_max = SIDEBAR_SCAN_Y_RANGE
        step = SIDEBAR_SCAN_STEP

        # ── 第 1 步: 全量扫描亮度 ──
        ys: list[float] = []
        brights: list[int] = []
        max_bright = 0
        sum_bright = 0

        y = y_min
        while y <= y_max:
            c = PixelChecker.get_pixel(screen, SIDEBAR_SCAN_X, y)
            brightness = c.r + c.g + c.b
            ys.append(y)
            brights.append(brightness)
            max_bright = max(max_bright, brightness)
            sum_bright += brightness
            y += step

        total_count = len(ys)
        if total_count == 0:
            _log.warning('[UI] 侧边栏扫描采样为空')
            return None

        avg_bright = sum_bright / total_count

        # ── 第 2 步: 自适应阈值 (0.70*峰值 / 均值+40, 比旧版 avg+80 宽松 2x) ──
        adaptive_threshold = max(int(max_bright * 0.70), int(avg_bright) + 40)

        # ── 第 3 步: 连续段 (≥2 step 合格) ──
        segments: list[list[tuple[float, int]]] = []  # [(y, brightness)]
        current: list[tuple[float, int]] = []
        prev_y: float | None = None

        for yy, br in zip(ys, brights, strict=True):
            if br >= adaptive_threshold:
                if prev_y is not None and (yy - prev_y) <= step * 1.5:
                    current.append((yy, br))
                else:
                    if current:
                        segments.append(current)
                    current = [(yy, br)]
                prev_y = yy
            else:
                if current:
                    segments.append(current)
                    current = []
                prev_y = None
        if current:
            segments.append(current)

        min_seg_steps = 2  # ≥2 个连续采样点 (≈0.02 高度) 才认为是高亮条
        valid = [seg for seg in segments if len(seg) >= min_seg_steps]
        segs_info = sorted(
            ((len(s), min(x[0] for x in s), max(x[0] for x in s)) for s in segments),
            reverse=True,
        )[:3]

        if not valid:
            _log.debug(
                '[UI] 侧边栏无有效高亮段 (segs={}, 最长段={}, max_br={} avg_br={} th={})',
                len(segments),
                segs_info[0] if segs_info else 'none',
                max_bright,
                int(avg_bright),
                adaptive_threshold,
            )
            return None

        # 取最长段, 以亮度加权求中心 (比纯平均更贴近高亮条峰值位置)
        longest = max(valid, key=len)
        cover = len(longest) / total_count
        if not (0.03 <= cover <= 0.60):
            _log.debug(
                '[UI] 侧边栏高亮段覆盖异常 cover={:.0%} (segs={} valid={}), 放弃',
                cover,
                len(segments),
                len(valid),
            )
            return None

        total_w = sum(x[1] for x in longest)
        if total_w <= 0:
            return None
        center = sum(x[0] * x[1] for x in longest) / total_w
        y_start = longest[0][0]
        y_end = longest[-1][0]
        _log.debug(
            '[UI] 侧边栏选中章 y={:.3f} (段长{}点 {:.3f}-{:.3f}, max_br={} avg_br={} th={} cover={:.0%})',
            center,
            len(longest),
            y_start,
            y_end,
            max_bright,
            int(avg_bright),
            adaptive_threshold,
            cover,
        )
        return center

    def read_chapter_slots(self, screen: np.ndarray | None = None) -> tuple[ChapterSlot, ...]:
        """读取固定章节槽位，返回章节编号和 OCR 置信度。"""
        if self._ocr is None:
            raise RuntimeError('需要 OCR 引擎才能读取章节槽位')
        if screen is None:
            screen = self._ctrl.screenshot()
        return recognize_chapter_slots(screen, self._ocr)

    # ── 地图标题读取 ──────────────────────────────────────────────────────

    @staticmethod
    def read_map(
        screen: np.ndarray,
        ocr: OCREngine,
    ) -> MapIdentity | None:
        """读取当前地图标题，并返回结构化地图标识。"""
        return recognize_map(screen, ocr)

    # ── 页面回退和面板动作 ────────────────────────────────────────────────

    def switch_panel(self, panel: MapPanel) -> None:
        """切换到指定面板标签并验证到达。"""
        current = self.read_active_panel(self._ctrl.screenshot())
        _log.info(
            '[UI] 地图页面: {} → {}',
            current.value if current else '未知',
            panel.value,
        )
        target_idx = PANEL_TO_INDEX[panel]
        source = f'地图-{current.value if current else "?"}'
        target = f'地图-{panel.value}'
        last_err: NavigationError | None = None

        for attempt in range(1, self._PANEL_SWITCH_MAX_RETRIES + 1):
            if attempt > 1:
                _log.warning(
                    '[UI] 面板切换重试 {}/{}: {} -> {} (等 {:.1f}s)',
                    attempt,
                    self._PANEL_SWITCH_MAX_RETRIES,
                    source,
                    target,
                    self._PANEL_SWITCH_RETRY_DELAY,
                )
                time.sleep(self._PANEL_SWITCH_RETRY_DELAY)

            try:
                click_and_wait_for_page(
                    self._ctrl,
                    click_coord=PANEL_POSITIONS[panel.name.lower()],
                    checker=make_tab_checker(TabbedPageType.MAP, target_idx),
                    source=source,
                    target=target,
                )
            except NavigationError as e:
                last_err = e
                _log.warning(
                    '[UI] 面板切换失败 ({}/{}): {} -> {}',
                    attempt,
                    self._PANEL_SWITCH_MAX_RETRIES,
                    source,
                    target,
                )
            else:
                return

        raise NavigationError(
            f'面板切换失败 (已重试 {self._PANEL_SWITCH_MAX_RETRIES} 次): {source} -> {target}',
            screen=self._ctrl.screenshot(),
        ) from last_err

    def ensure_panel(self, panel: MapPanel) -> None:
        """确保当前处于指定面板，若不是则切换。"""
        screen = self._ctrl.screenshot()
        if self.read_active_panel(screen) != panel:
            self.switch_panel(panel)

    def click_expedition_skip(self) -> None:
        """点击屏幕右侧 — 用于跳过远征动画。"""
        self._ctrl.click(*CLICK_EXPEDITION_SKIP)

    # ── 页面回退 ──────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击回退按钮 (◁)，返回母港主页。"""
        from autowsgr.application.ui.controller.home.main_page import HomePage

        _log.info('[UI] 地图页面 → 回退')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=CLICK_BACK,
            checker=HomePage.check_current_page,
            source=PageName.MAP,
            target=PageName.HOME,
        )
