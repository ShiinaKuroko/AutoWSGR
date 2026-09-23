"""编排 sortie_page 页面壳、顶部标签和页面回退。

上层调用：
- application.ui.controller.operations.sortie_page.*_page：选择顶部业务标签。
- application.ui.navigation、application.ui.controller.home.main_page：进入或离开页面壳。

下层依赖：
- application.ui.controller.operations.sortie_page.main_page.constants：提供页面坐标校准。
- application.ui.controller.operations.sortie_page.main_page.page：提供标签业务类型和顺序。
- application.ui.controller.operations.sortie_page.main_page.recognition：提供页面事实和导航检查器。
- common.device.interaction：执行点击、等待和导航失败收口。

边界：
本模块只拥有注入的 UI 上下文并编排页面壳流程，不实现图像识别或跨任务调度。
"""

from __future__ import annotations

import enum
import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    constants,
    recognition,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.interaction import NavigationError, click_and_wait_for_page


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.application.ui.navigation.types import PageMatch


_log = get_logger('ui.sortie.main_page')


# ── 标签切换参数 ─────────────────────────────────────────────────────────────────────

_TAB_SWITCH_MAX_RETRIES = 3  # 标签切换失败时的最大重试次数。
_TAB_SWITCH_RETRY_DELAY = 1.0  # 标签切换重试前的等待时间（秒）。


class TabbedPageType(enum.Enum):
    """共享标签页页面类型。"""

    MAP = PageName.MAP
    BUILD = PageName.BUILD
    INTENSIFY = PageName.INTENSIFY
    MISSION = PageName.MISSION
    FRIEND = PageName.FRIEND


class SortieTab(enum.Enum):
    """sortie_page 顶部的五个业务标签。"""

    SORTIE = '出征'
    EXERCISE = '演习'
    EXPEDITION = '远征'
    CAMPAIGN = '战役'
    DECISIVE = '决战'


SORTIE_TAB_LIST: tuple[SortieTab, ...] = tuple(SortieTab)
"""顶部标签的显示顺序。"""

SORTIE_TAB_INDEX: dict[SortieTab, int] = {tab: index for index, tab in enumerate(SORTIE_TAB_LIST)}
"""顶部标签到视觉索引的映射。"""


class SortiePage:
    """sortie_page 页面壳的控制器。"""

    def __init__(self, ctx: UIContext) -> None:
        """保存调用方注入的 UI 上下文和设备控制器。

        Args:
            ctx: 当前运行时 UI 上下文。
        """
        self._ctx = ctx
        self._ctrl = ctx.ctrl
        self._ocr = ctx.ocr

    # ── 页面检查 ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否已经进入 sortie_page 页面壳。

        Args:
            screen: RGB 截图。

        Returns:
            sortie_page 顶部标签栏的页面匹配结果。
        """
        return recognition.check_tabbed_page(screen, TabbedPageType.MAP.value)

    @staticmethod
    def check_expedition_notification(screen: np.ndarray) -> bool:
        """检查 sortie_page 顶部是否显示远征完成通知。

        Args:
            screen: sortie_page 当前截图。

        Returns:
            顶部远征通知命中时返回 True。
        """
        return recognition.check_expedition_notification(screen)

    @staticmethod
    def read_active_tab(screen: np.ndarray) -> SortieTab | None:
        """读取 sortie_page 当前选中的业务标签。

        Args:
            screen: sortie_page 当前截图。

        Returns:
            当前选中的出征标签；无法识别时返回 None。
        """
        index = recognition.read_active_tab_index(screen)
        if index is None or index >= len(SORTIE_TAB_LIST):
            return None
        return SORTIE_TAB_LIST[index]

    # ── 顶部标签流程 ────────────────────────────────────────────────────────────────

    def click_tab(self, tab: SortieTab) -> None:
        """点击目标顶部标签并确认 sortie_page 仍处于目标标签。

        Args:
            tab: 要打开的出征业务标签。

        Raises:
            NavigationError: 多次点击后仍未到达目标标签。
        """
        current = self.read_active_tab(self._ctrl.screenshot())
        target_index = SORTIE_TAB_INDEX[tab]
        source = f'sortie_page-{current.value if current else "unknown"}'
        target = f'sortie_page-{tab.value}'
        checker = recognition.create_tab_checker(TabbedPageType.MAP.value, target_index)
        last_error: NavigationError | None = None
        _log.info('[UI] 出征页 → 切换标签：目标={!r}，状态=开始', tab.value)

        for attempt in range(1, _TAB_SWITCH_MAX_RETRIES + 1):
            if attempt > 1:
                time.sleep(_TAB_SWITCH_RETRY_DELAY)
            try:
                click_and_wait_for_page(
                    self._ctrl,
                    click_coord=constants.TAB_POSITIONS[tab.name.lower()],
                    checker=checker,
                    source=source,
                    target=target,
                )
            except NavigationError as error:
                last_error = error
                if attempt < _TAB_SWITCH_MAX_RETRIES:
                    _log.warning(
                        '[UI] 出征页 → 重试：目标={!r}，尝试次数={}，最大尝试次数={}，原因={!r}',
                        tab.value,
                        attempt,
                        _TAB_SWITCH_MAX_RETRIES,
                        '未到达目标页面',
                    )
            else:
                _log.info('[UI] 出征页 → 切换标签：目标={!r}，结果=成功', tab.value)
                return

        _log.error(
            '[UI] 出征页 → 终止：目标={!r}，尝试次数={}，原因={!r}，结果=失败',
            tab.value,
            _TAB_SWITCH_MAX_RETRIES,
            '未到达目标页面',
        )
        raise NavigationError(
            f'顶部标签切换失败：source={source!r}，target={target!r}，'
            f'attempts={_TAB_SWITCH_MAX_RETRIES}',
            screen=self._ctrl.screenshot(),
        ) from last_error

    def select_tab(self, tab: SortieTab) -> None:
        """确保 sortie_page 当前处于目标顶部标签。

        Args:
            tab: 需要处于选中状态的出征业务标签。
        """
        if self.read_active_tab(self._ctrl.screenshot()) != tab:
            self.click_tab(tab)

    # ── 页面回退 ─────────────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """从 sortie_page 页面壳返回母港主页。

        Raises:
            NavigationError: 点击返回后未确认回到母港主页。
        """
        # 局部导入避免主页和 sortie_page 的页面包初始化循环。
        from autowsgr.application.ui.controller.home.main_page import HomePage

        _log.info('[UI] 出征页 → 返回：状态=开始')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=HomePage.check_current_page,
            source=PageName.MAP.value,
            target=PageName.HOME.value,
        )
        _log.info('[UI] 出征页 → 返回：结果=成功')
