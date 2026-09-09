"""模块功能：负责建造页面标签、建造收取和舰船解体操作。

上层调用：
- business.logistics.build：调用标签选择、建造收取和新建造入口。
- business.logistics.destroy：调用解体标签和解装流程入口。
- application.ui.navigation.registry：注册建造页面检查器。

下层依赖：
- application.ui.controller.sidebar.build_page.constants：提供建造页面专用坐标。
- application.ui.controller.shared.top_tabs：识别标签页和生成标签检查器。
- common.ui.interaction：执行点击后的页面到达等待。
- common.vision：匹配建造结果、资源页面和确认弹窗。
- common.types：提供页面名称和舰种枚举。
"""

from __future__ import annotations

import enum
import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.shared.top_tabs import (
    TabbedPageType,
    check_tabbed_page,
    get_active_tab_index,
    make_tab_checker,
)
from autowsgr.application.ui.controller.sidebar.build_page import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName, ShipType
from autowsgr.common.ui.interaction import click_and_wait_for_page
from autowsgr.common.vision import ImageChecker, PageMatch
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('ui')

# ── 页面标签 ─────────────────────────────────────────────────────────────────


class BuildTab(enum.Enum):
    """建造页面标签组。"""

    BUILD = '建造'
    DESTROY = '解体'
    DEVELOP = '开发'
    DISCARD = '废弃'


_TAB_ORDER: tuple[BuildTab, ...] = tuple(BuildTab)
_TAB_TO_INDEX: dict[BuildTab, int] = {tab: index for index, tab in enumerate(_TAB_ORDER)}


class BuildPage:
    """建造页面及其解体、开发、废弃标签的 UI 操作控制器。"""

    def __init__(self, ctx: GameContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面检查 ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """检查截图是否属于建造页面组。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            包含建造标签栏的页面匹配结果。
        """
        return check_tabbed_page(screen, TabbedPageType.BUILD)

    @staticmethod
    def read_active_tab(screen: np.ndarray) -> BuildTab | None:
        """读取建造页面当前激活的标签。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            当前标签；索引无法识别或越界时返回 ``None``。
        """
        index = get_active_tab_index(screen)
        if index is None or index >= len(_TAB_ORDER):
            return None
        return _TAB_ORDER[index]

    # ── 标签选择 ──────────────────────────────────────────────────────────────

    def select_tab(self, tab: BuildTab) -> None:
        """选择指定标签并确认目标标签到达。

        Args:
            tab: 目标标签。

        Raises:
            NavigationError: 超时未到达目标标签。
        """
        current = self.read_active_tab(self._ctrl.screenshot())
        _log.info(
            '[UI] 建造页面: {} → {}',
            current.value if current else '未知',
            tab.value,
        )
        target_idx = _TAB_TO_INDEX[tab]
        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.TAB_POSITIONS[tab.name.lower()],
            checker=make_tab_checker(TabbedPageType.BUILD, target_idx),
            source=f'建造-{current.value if current else "?"}',
            target=f'建造-{tab.value}',
        )

    # ── 页面返回 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击返回按钮，离开建造页面并回到侧边栏或主页面。

        Args:
            None.

        Returns:
            None. 页面到达侧边栏或主页面后返回。

        Raises:
            NavigationError: 超时仍未离开建造页面。
        """
        from autowsgr.application.ui.controller.home.main_page import HomePage
        from autowsgr.application.ui.controller.sidebar.main_page import SidebarPage

        _log.info('[UI] 建造页面 → 返回侧边栏')

        def _checker(screen: np.ndarray) -> bool:
            return SidebarPage.check_current_page(screen) or HomePage.check_current_page(screen)

        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=_checker,
            source=PageName.BUILD,
            target=f'{PageName.SIDEBAR}/{PageName.HOME}',
        )

    # ── 建造原子动作 ──────────────────────────────────────────────────────────

    def click_slot(self, slot: int) -> None:
        """点击指定建造槽位。

        Args:
            slot: 槽位编号，范围为 1-4。

        Raises:
            ValueError: 槽位编号不在 1-4 范围内。
        """
        if not 1 <= slot <= 4:
            raise ValueError(f'建造槽位必须为 1-4，收到: {slot}')
        _log.info('[UI] 建造页面 → 点击槽位 {}', slot)
        self._ctrl.click(*constants.SLOT_POSITIONS[slot - 1])
        time.sleep(0.5)

    def collect_slot(self, slot: int) -> None:
        """点击指定槽位并等待建造结果动画出现。

        Args:
            slot: 槽位编号，范围为 1-4。
        """
        _log.info('[UI] 建造页面 → 收取槽位 {}', slot)
        self.click_slot(slot)
        time.sleep(1.0)

    def fast_build_slot(self, slot: int) -> None:
        """点击指定槽位并进入快速建造确认流程。

        Args:
            slot: 槽位编号，范围为 1-4。
        """
        _log.info('[UI] 建造页面 → 快速建造槽位 {}', slot)
        self.click_slot(slot)
        time.sleep(0.5)

    def start_build(self) -> None:
        """在当前标签下启动建造。

        资源配方调整由上层流程负责；本方法只提交当前资源选择页面。

        Args:
            None.

        Returns:
            None. 点击确认后等待页面动画稳定。
        """
        _log.info('[UI] 建造页面 → 确认建造')
        self._ctrl.click(*constants.CLICK_CONFIRM)
        time.sleep(1.0)

    def click_skip_animation(self) -> None:
        """点击跳过建造结果动画。

        Args:
            None.

        Returns:
            None.
        """
        self._ctrl.click(*constants.CLICK_DISMISS_ANIMATION)

    # ── 拆解原子动作 ──────────────────────────────────────────────────────────

    def click_destroy_add(self) -> None:
        """点击解体标签的添加按钮，打开待解装舰船选择。"""
        _log.info('[UI] 建造页面 (解体) → 添加')
        self._ctrl.click(*constants.CLICK_DESTROY_ADD)

    def click_destroy_quick_select(self) -> None:
        """点击解体标签的快速选择按钮，批量选择舰船。"""
        _log.info('[UI] 建造页面 (解体) → 快速选择')
        self._ctrl.click(*constants.CLICK_DESTROY_QUICK_SELECT)

    def confirm_destroy_select(self) -> None:
        """确认解体标签中的舰船选择。"""
        _log.info('[UI] 建造页面 (解体) → 确认选择')
        self._ctrl.click(*constants.CLICK_DESTROY_CONFIRM_SELECT)

    def click_destroy_remove_equip(self) -> None:
        """点击解体标签的卸下装备选项。"""
        _log.info('[UI] 建造页面 (解体) → 卸下装备')
        self._ctrl.click(*constants.CLICK_DESTROY_REMOVE_EQUIP)

    def confirm_destroy(self) -> None:
        """确认解体标签中的解装操作。"""
        _log.info('[UI] 建造页面 (解体) → 解装确认')
        self._ctrl.click(*constants.CLICK_DESTROY_CONFIRM)

    def confirm_destroy_four_star(self) -> None:
        """确认解体标签中的高星舰船警告。"""
        _log.info('[UI] 建造页面 (解体) → 四星确认')
        self._ctrl.click(*constants.CLICK_DESTROY_FOUR_STAR_CONFIRM)

    def open_destroy_type_filter(self) -> None:
        """打开解体标签的舰船类型过滤器。"""
        _log.info('[UI] 建造页面 (解体) → 打开类型过滤')
        self._ctrl.click(*constants.CLICK_DESTROY_TYPE_FILTER)

    def confirm_destroy_filter(self) -> None:
        """确认解体标签的舰船类型过滤条件。"""
        _log.info('[UI] 建造页面 (解体) → 确认过滤')
        self._ctrl.click(*constants.CLICK_DESTROY_CONFIRM_FILTER)

    # ── 建造组合动作 ──────────────────────────────────────────────────────────

    def dismiss_build_result(self) -> None:
        """处理建造完成后的获取动画和确认弹窗。

        Args:
            None.

        Returns:
            None. 连续获取标志消失后返回。
        """
        get_ship_templates = [Templates.Symbol.GET_SHIP, Templates.Symbol.GET_ITEM]
        for _ in range(10):
            screen = self._ctrl.screenshot()
            if not ImageChecker.template_exists(screen, get_ship_templates):
                break
            self.click_skip_animation()
            time.sleep(0.5)
            screen = self._ctrl.screenshot()
            detail = ImageChecker.find_any(screen, Templates.Confirm.all())
            if detail is not None:
                self._ctrl.click(*detail.center)
                time.sleep(0.5)

    def collect_all(
        self,
        build_type: str = 'ship',
        *,
        allow_fast_build: bool = False,
    ) -> int:
        """收取已建造完成的舰船或装备。

        Args:
            build_type: 建造类型，`ship` 表示舰船，其他值表示装备。
            allow_fast_build: 是否先处理可快速建造的槽位。

        Returns:
            实际收取的数量。

        Raises:
            RuntimeError: 对应仓库已满。
        """
        collected = 0

        if allow_fast_build:
            fast_tmpl = (
                Templates.Build.SHIP_FAST if build_type == 'ship' else Templates.Build.EQUIP_FAST
            )
            for _ in range(4):
                screen = self._ctrl.screenshot()
                detail = ImageChecker.find_template(screen, fast_tmpl)
                if detail is None:
                    break
                self._ctrl.click(*detail.center)
                time.sleep(0.3)
                screen = self._ctrl.screenshot()
                confirm = ImageChecker.find_any(screen, Templates.Confirm.all())
                if confirm is not None:
                    self._ctrl.click(*confirm.center)
                    time.sleep(1.0)

        complete_tmpl = (
            Templates.Build.SHIP_COMPLETE
            if build_type == 'ship'
            else Templates.Build.EQUIP_COMPLETE
        )
        full_depot_tmpl = (
            Templates.Build.SHIP_FULL_DEPOT
            if build_type == 'ship'
            else Templates.Build.EQUIP_FULL_DEPOT
        )

        for _ in range(4):
            screen = self._ctrl.screenshot()
            detail = ImageChecker.find_template(screen, complete_tmpl)
            if detail is None:
                break
            if ImageChecker.template_exists(screen, full_depot_tmpl):
                raise RuntimeError(f'{build_type} 仓库已满')
            self._ctrl.click(*detail.center)
            time.sleep(1.0)
            self.dismiss_build_result()
            collected += 1

        _log.info('[UI] 建造收取: {} 艘 ({})', collected, build_type)
        return collected

    def start_new_build(self, build_type: str = 'ship') -> None:
        """在当前标签启动一次新建造。

        Args:
            build_type: 建造类型，`ship` 表示舰船，其他值表示装备。

        Raises:
            RuntimeError: 建造队列已满或资源选择页面未出现。
        """
        start_tmpl = (
            Templates.Build.SHIP_START if build_type == 'ship' else Templates.Build.EQUIP_START
        )
        screen = self._ctrl.screenshot()
        detail = ImageChecker.find_template(screen, start_tmpl)
        if detail is None:
            raise RuntimeError(f'{build_type} 建造队列已满')

        self._ctrl.click(*detail.center)
        time.sleep(1.0)

        resource_tmpl = Templates.Build.RESOURCE
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            screen = self._ctrl.screenshot()
            if ImageChecker.template_exists(screen, resource_tmpl):
                break
            time.sleep(0.3)
        else:
            raise RuntimeError('资源选择页面未出现')

        self._ctrl.click(*constants.CLICK_CONFIRM)
        time.sleep(1.0)
        _log.info('[UI] 建造已启动 ({})', build_type)

    # ── 拆解组合动作 ──────────────────────────────────────────────────────────

    def destroy_ships(
        self,
        ship_types: list[ShipType] | None = None,
        *,
        remove_equipment: bool = True,
    ) -> None:
        """在解体标签上执行完整解装流程。

        Args:
            ship_types: 要解体的舰种列表；`None` 表示不过滤舰种。
            remove_equipment: 是否在解装前卸下装备。

        Returns:
            None. 解装确认流程完成后返回。
        """
        _step_delay = 1.5

        self.click_destroy_add()
        time.sleep(_step_delay)

        if ship_types:
            # 按舰种过滤：打开过滤器 → 勾选各舰种 → 确认
            self.open_destroy_type_filter()
            time.sleep(_step_delay)
            for ship_type in ship_types:
                _log.debug('[UI] 解体 → 点击舰种: {}', ship_type.value)
                self._ctrl.click(*constants.DESTROY_TYPE_POSITIONS[ship_type.name])
                time.sleep(0.8)
            self.confirm_destroy_filter()
            time.sleep(_step_delay)

        self.click_destroy_quick_select()
        time.sleep(_step_delay)
        self.confirm_destroy_select()
        time.sleep(_step_delay)
        if remove_equipment:
            self.click_destroy_remove_equip()
            time.sleep(_step_delay)
        self.confirm_destroy()
        time.sleep(_step_delay)
        self.confirm_destroy_four_star()
        time.sleep(_step_delay)

        _log.info(
            '[UI] 解装完成 (舰种={}, 卸下装备={})',
            [t.value for t in ship_types] if ship_types else '全部',
            remove_equipment,
        )
