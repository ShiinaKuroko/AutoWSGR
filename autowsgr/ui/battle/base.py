"""出征准备页面基类 — 声明共享依赖与公共查询 / 导航方法。

所有准备页 Mixin 均继承 :class:`BaseBattlePreparation`，
最终由 :class:`~autowsgr.ui.battle.preparation.BattlePreparationPage` 组合。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.image_resources import Templates
from autowsgr.infra.base.constants.coordinates import point
from autowsgr.infra.base.constants.signatures import signature
from autowsgr.infra.logger import get_logger
from autowsgr.types import PageName
from autowsgr.ui.battle.constants import (
    AUTO_SUPPLY_ON,
    AUTO_SUPPLY_PROBE,
    CLICK_AUTO_SUPPLY,
    CLICK_BACK,
    CLICK_FLEET,
    CLICK_SHIP_SLOT,
    CLICK_START_BATTLE,
    FLEET_ACTIVE,
    FLEET_PROBE,
    PANEL_ACTIVE,
    STATE_TOLERANCE,
)
from autowsgr.ui.utils import click_and_wait_for_page
from autowsgr.vision import (
    ImageChecker,
    PageMatch,
    PixelChecker,
)


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.context import GameContext
    from autowsgr.vision import OCREngine

_log = get_logger('ui.preparation')


# ═══════════════════════════════════════════════════════════════════════════════
# 枚举
# ═══════════════════════════════════════════════════════════════════════════════


class RepairStrategy(enum.Enum):
    """修理策略。"""

    MODERATE = 'moderate'
    """修中破及以上 (damage >= 1)。"""

    SEVERE = 'severe'
    """仅修大破 (damage >= 2)。"""

    ALWAYS = 'always'
    """有损伤即修 (damage >= 1, 含黄血)。"""

    NEVER = 'never'
    """不修理。"""


class Panel(enum.Enum):
    """出征准备底部面板标签。"""

    STATS = '综合战力'
    QUICK_SUPPLY = '快速补给'
    QUICK_REPAIR = '快速修理'
    EQUIPMENT = '装备预览'


PANEL_PROBE: dict[Panel, tuple[float, float]] = {
    panel: point('battle_prep', f'panel_probe.{panel.name.lower()}') for panel in Panel
}
"""面板标签探测点 — 数据源: coordinates/battle_prep.yaml。选中项探测颜色 ≈ (30, 139, 240)。"""

CLICK_PANEL: dict[Panel, tuple[float, float]] = {
    panel: point('battle_prep', f'click_panel.{panel.name.lower()}') for panel in Panel
}
"""面板标签点击位置 — 数据源: coordinates/battle_prep.yaml。"""

PAGE_SIGNATURE = signature('battle_prep', 'page')
"""出征准备页面像素签名 — 数据源: signatures/battle_prep.yaml。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 基类
# ═══════════════════════════════════════════════════════════════════════════════


class BaseBattlePreparation:
    """出征准备页面基类。

    声明所有 Mixin 需要的共享依赖与公共查询 / 导航方法。

    Parameters
    ----------
    ctx:
        游戏上下文。
    ocr:
        OCR 引擎实例 (可选)。
    """

    def __init__(self, ctx: GameContext, ocr: OCREngine | None = None) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl
        self._ocr = ocr or ctx.ocr
        self._ship_ocr = getattr(ctx, 'ship_ocr', None)

    @property
    def _preferred_ocr(self) -> OCREngine | None:
        """返回船只识别优先使用的 OCR 引擎。

        增强船只识别 (FastOCR) 开启时优先使用它，未开启时回退默认 OCR。
        只有名称 / 等级 / 舰种等船只信息节点应使用本属性，其余节点仍用 ``_ocr``。
        """
        return self._ship_ocr or self._ocr

    # ── 页面识别 ──────────────────────────────────────────────────────────

    @staticmethod
    def is_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否为出征准备页面。

        用出征准备页面独有特征模板匹配 (迁移自 classic ``fight_prepare_page``,
        183x48 局部特征), 返回带置信度的 :class:`PageMatch` 供候选集排序。
        """
        result = ImageChecker.find_template(screen, Templates.Page.BATTLE_PREP, confidence=0.85)
        name = PageName.BATTLE_PREP.value
        if result is None:
            return PageMatch(name=name, matched=False, score=0.0)
        return PageMatch(name=name, matched=True, score=result.confidence)

    # ── 状态查询 — 舰队 / 面板 ────────────────────────────────────────────

    @staticmethod
    def get_selected_fleet(screen: np.ndarray) -> int | None:
        """获取当前选中的舰队编号 (1-4)。"""
        for fleet_id, (x, y) in FLEET_PROBE.items():
            pixel = PixelChecker.get_pixel(screen, x, y)
            if pixel.near(FLEET_ACTIVE, STATE_TOLERANCE):
                return fleet_id
        return None

    @staticmethod
    def get_active_panel(screen: np.ndarray) -> Panel | None:
        """获取当前激活的底部面板。"""
        for panel, (x, y) in PANEL_PROBE.items():
            pixel = PixelChecker.get_pixel(screen, x, y)
            if pixel.near(PANEL_ACTIVE, STATE_TOLERANCE):
                return panel
        return None

    @staticmethod
    def is_auto_supply_enabled(screen: np.ndarray) -> bool:
        """检测自动补给是否启用。"""
        x, y = AUTO_SUPPLY_PROBE
        return PixelChecker.get_pixel(screen, x, y).near(AUTO_SUPPLY_ON, STATE_TOLERANCE)

    # ── 动作 — 回退 / 出征 ───────────────────────────────────────────────

    def go_back(self) -> None:
        """点击回退按钮 (◁)，返回地图页面。

        用**到达验证** (:func:`click_and_wait_for_page`): 点击后确认真的到了
        地图页面。此前用 ``wait_leave_page`` 语义 (checker 为 False 即"已离开")
        存在假成功——点击后画面仍在出征准备页时, ``MapPage.is_current_page``
        同样为 False, 第一帧就误判离开, 从未验证到达。
        """
        from autowsgr.ui.map import MapPage

        _log.debug('[UI] 出征准备 → 回退')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=CLICK_BACK,
            checker=MapPage.is_current_page,
            source=PageName.BATTLE_PREP,
            target=PageName.MAP,
        )

    def start_battle(self) -> None:
        """点击「开始出征」按钮。"""
        _log.info('[UI] 出征准备 → 开始出征')
        self._ctrl.click(*CLICK_START_BATTLE)

    # ── 动作 — 舰队 / 面板选择 ───────────────────────────────────────────

    def select_fleet(self, fleet: int) -> None:
        """选择舰队 (1-4)。"""
        if fleet not in CLICK_FLEET:
            raise ValueError(f'舰队编号必须为 1-4，收到: {fleet}')
        _log.debug('[UI] 出征准备 → 选择 {}队', fleet)
        self._ctrl.click(*CLICK_FLEET[fleet])

    def select_panel(self, panel: Panel) -> None:
        """切换底部面板标签。"""
        _log.debug('[UI] 出征准备 → {}', panel.value)
        self._ctrl.click(*CLICK_PANEL[panel])

    def quick_supply(self) -> None:
        """点击「快速补给」标签。"""
        self.select_panel(Panel.QUICK_SUPPLY)

    def quick_repair(self) -> None:
        """点击「快速修理」标签。"""
        self.select_panel(Panel.QUICK_REPAIR)

    # ── 动作 — 舰船槽位 ─────────────────────────────────────────────────

    def click_ship_slot(self, slot: int) -> None:
        """点击指定舰船槽位 (0-5)。"""
        if slot not in CLICK_SHIP_SLOT:
            raise ValueError(f'舰船槽位必须为 0-5，收到: {slot}')
        _log.debug('[UI] 出征准备 → 点击舰船位 {}', slot)
        self._ctrl.click(*CLICK_SHIP_SLOT[slot])

    # ── 动作 — 开关 ──────────────────────────────────────────────────────

    def toggle_auto_supply(self) -> None:
        """切换自动补给开关。"""
        _log.debug('[UI] 出征准备 → 切换自动补给')
        self._ctrl.click(*CLICK_AUTO_SUPPLY)
