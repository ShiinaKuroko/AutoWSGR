"""模块功能：负责建造页面检查、建造流程和舰船解体流程入口。

上层调用：
- business.logistics.build：调用建造流程入口。
- business.logistics.destroy：调用解体流程入口。
- application.ui.navigation.registry：注册建造页面检查器。

下层依赖：
- application.ui.controller.sidebar.build_page.constants：提供建造页面专用坐标。
- application.ui.controller.sidebar.build_page.operations：执行标签切换操作。
- application.ui.controller.sidebar.build_page.workflow：编排建造、收取和解装流程。
- application.ui.controller.operations.sortie_page.main_page：提供建造页面识别。
- common.system.logger：提供页面动作日志。
- common.device.interaction：执行点击后的页面到达等待。
- common.types：提供页面名称和舰种类型。
- common.vision：提供页面匹配结果类型。

本模块只提供建造页面检查、标签导航、完整业务入口和页面返回，不负责原子设备操作、
视觉识别细节、任务调度或业务配置读取。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    TabbedPageType,
    check_tabbed_page,
    create_tab_checker,
)
from autowsgr.application.ui.controller.sidebar.build_page import constants, operations, workflow
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.interaction import click_and_wait_for_page


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.business.combat.types import ShipType
    from autowsgr.application.ui.navigation.types import PageMatch


_log = get_logger('ui.sidebar.build_page')

# ── 页面标签 ─────────────────────────────────────────────────────────────────


class BuildTab(enum.Enum):
    """建造页面标签组。"""

    BUILD = '建造'
    DESTROY = '解体'
    DEVELOP = '开发'
    DISCARD = '废弃'


# TODO(build-page): 开发、废弃尚未形成独立业务流程，待操作和成功终态契约确定后补齐。
_TAB_ORDER: tuple[BuildTab, ...] = tuple(BuildTab)
_TAB_TO_INDEX: dict[BuildTab, int] = {tab: index for index, tab in enumerate(_TAB_ORDER)}


class BuildPage:
    """建造页面及其解体、开发、废弃标签的 UI 操作控制器。"""

    def __init__(self, ctx: UIContext) -> None:
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

    # ── 建造流程 ──────────────────────────────────────────────────────────────

    def build(
        self,
        *,
        build_count: int = 1,
        collect_completed: bool = True,
        build_type: str = 'ship',
        allow_fast_build: bool = False,
    ) -> int:
        """切换到对应标签并执行收取、建造流程。

        Args:
            build_count: 要新建的数量，必须为非负整数。
            collect_completed: 是否先收取已完成的建造项目。
            build_type: 建造类型，`ship` 表示舰船，其他值表示装备。
            allow_fast_build: 是否先处理可快速建造的槽位。

        Returns:
            实际收取的数量。

        Raises:
            NavigationError: 超时未切换到目标标签。
            TypeError: build_count 不是整数。
            ValueError: build_count 小于零。
            RuntimeError: 建造队列已满、仓库已满或资源页面未出现。
        """
        if not isinstance(build_count, int) or isinstance(build_count, bool):
            _log.error(
                '[UI] 建造页 → 拒绝建造：建造数量={!r}，期望类型=非负整数，结果=拒绝',
                build_count,
            )
            raise TypeError(f'建造数量必须为整数，收到: {build_count!r}')
        if build_count < 0:
            _log.error(
                '[UI] 建造页 → 拒绝建造：建造数量={!r}，期望范围=>=0，结果=拒绝',
                build_count,
            )
            raise ValueError(f'建造数量不能为负数，收到: {build_count}')

        target_tab = BuildTab.BUILD if build_type == 'ship' else BuildTab.DEVELOP
        _log.info(
            '[UI] 建造页 → 切换标签：目标={}，状态=开始',
            target_tab.value,
        )
        operations.select_tab(
            self._ctrl,
            click_coord=constants.TAB_POSITIONS[target_tab.name.lower()],
            checker=create_tab_checker(TabbedPageType.BUILD, _TAB_TO_INDEX[target_tab]),
            source=PageName.BUILD,
            target=f'{PageName.BUILD}-{target_tab.value}',
        )
        _log.info('[UI] 建造页 → 切换标签：目标={}，结果=成功', target_tab.value)
        return workflow.build(
            self._ctrl,
            build_count=build_count,
            collect_completed=collect_completed,
            build_type=build_type,
            allow_fast_build=allow_fast_build,
        )

    def destroy_ships(
        self,
        ship_types: list[ShipType] | None = None,
        *,
        remove_equipment: bool = True,
    ) -> None:
        """切换到解体标签并执行完整解装流程。

        Args:
            ship_types: 要解体的舰种列表；`None` 表示不过滤舰种。
            remove_equipment: 是否在解装前卸下装备。

        Raises:
            NavigationError: 超时未切换到解体标签。
        """
        target_tab = BuildTab.DESTROY
        _log.info('[UI] 建造页 → 切换标签：目标={}，状态=开始', target_tab.value)
        operations.select_tab(
            self._ctrl,
            click_coord=constants.TAB_POSITIONS[target_tab.name.lower()],
            checker=create_tab_checker(TabbedPageType.BUILD, _TAB_TO_INDEX[target_tab]),
            source=PageName.BUILD,
            target=f'{PageName.BUILD}-{target_tab.value}',
        )
        _log.info('[UI] 建造页 → 切换标签：目标={}，结果=成功', target_tab.value)
        workflow.destroy_ships(
            self._ctrl,
            ship_types=ship_types,
            remove_equipment=remove_equipment,
        )

    # ── 标签切换 ──────────────────────────────────────────────────────────────

    def go_to_tab(self, tab: BuildTab) -> None:
        """点击顶部标签，切到对应内容。

        只负责点击；是否真的切过去了由导航器用标签的 checker 确认。

        Args:
            tab: 目标标签。

        Raises:
            ValueError: 标签没有配置落点。
        """
        position = constants.TAB_POSITIONS.get(tab.name.lower())
        if position is None:
            raise ValueError(f'建造页没有该标签的落点: {tab!r}')
        _log.info('[UI] 建造页面 → 切换标签：tab={!r}，position={!r}', tab.value, position)
        self._ctx.ctrl.click(*position)

    # ── 页面返回 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击返回按钮，离开建造页面并回到侧边栏或主页面。

        Raises:
            NavigationError: 超时仍未离开建造页面。
        """
        # 延迟导入，避免侧边栏和主页模块反向加载建造页面。
        from autowsgr.application.ui.controller.home.main_page import HomePage
        from autowsgr.application.ui.controller.sidebar.main_page import SidebarPage

        _log.info('[UI] 建造页 → 回侧边：目标=侧边栏/主页面，状态=开始')

        def _checker(screen: np.ndarray) -> bool:
            return SidebarPage.check_current_page(screen) or HomePage.check_current_page(screen)

        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=_checker,
            source=PageName.BUILD,
            target=f'{PageName.SIDEBAR}/{PageName.HOME}',
        )
        _log.info('[UI] 建造页 → 回侧边：目标=侧边栏/主页面，结果=成功')
