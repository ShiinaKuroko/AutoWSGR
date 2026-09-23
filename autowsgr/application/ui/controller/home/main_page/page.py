"""编排主页导航和浮窗处理流程。

页面控制器持有完整的主页流程和导航契约；识别事实由 recognition.py 提供，
原子设备操作由 operations.py 提供，多阶段浮窗流程由 workflow.py 提供。
"""

from __future__ import annotations

import enum
import time
from typing import TYPE_CHECKING

from autowsgr.application.ui import recognition_flow
from autowsgr.application.ui.controller.home.main_page import (
    constants,
    recognition,
    workflow,
)
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.common.system.errors import ApplicationError
from autowsgr.common.system.logger import get_logger
from autowsgr.dispatch.context import HomeCheckObservation


if TYPE_CHECKING:
    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui.home.main_page')


# -- 主页流程参数 ------------------------------------------------------------

_OVERLAY_CLEAN_DELAY_SECONDS = 0.5
_EVENT_NAVIGATION_MAX_RETRIES = 3
_OVERLAY_FLOW_STEPS = 3


# -- 主页导航目标 ------------------------------------------------------------


class Target(enum.Enum):
    """主页导航契约支持的目标页面。"""

    SORTIE = '出征'
    TASK = '任务'
    SIDEBAR = '侧边栏'
    BACKYARD = '后院'
    EVENT = '活动'

    @property
    def page_name(self) -> PageName:
        """返回导航器使用的页面名称。"""
        return _TARGET_PAGES[self]


_TARGET_PAGES: dict[Target, PageName] = {
    Target.SORTIE: PageName.MAP,
    Target.TASK: PageName.MISSION,
    Target.SIDEBAR: PageName.SIDEBAR,
    Target.BACKYARD: PageName.BACKYARD,
    Target.EVENT: PageName.EVENT_MAP,
}


class HomePage:
    """负责主页浮窗流程和页面导航的控制器。"""

    def __init__(self, ctx: UIContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # -- 完整浮窗流程 --------------------------------------------------------

    def dismiss_current_overlay(
        self,
        *,
        attempt: int | None = None,
        navigation_context: ContextHandle | None = None,
    ) -> bool:
        """按优先级处理主页浮窗并确认页面回到稳定状态。

        Args:
            attempt: 当前外层主页检查的尝试次数。
            navigation_context: 负责保存导航截图和结果的 Context。

        Returns:
            至少处理一个浮窗时返回 ``True``，没有浮窗时返回 ``False``。

        Raises:
            workflow.HomeOverlayError: 浮窗无法到达终态时抛出。
        """
        _log.info(
            '[UI] 主页 → 处理浮窗：尝试次数={}，状态=开始',
            attempt if attempt is not None else 1,
        )
        handled = False
        record_screenshot = (
            navigation_context.record_screenshot
            if navigation_context is not None
            else getattr(self._ctx, 'record_screenshot', None)
        )
        if record_screenshot is None:
            raise RuntimeError('主页识别流程必须绑定 Context 截图记录回调')

        try:
            # 1. 按浮窗优先级识别当前页面状态。
            for step in range(1, _OVERLAY_FLOW_STEPS + 1):
                overlay = recognition_flow.recognize_with_retry(
                    self._ctrl,
                    recognition.read_overlay_match,
                    record_screenshot=record_screenshot,
                )
                if not overlay.satisfied:
                    _log.info(
                        '[UI] 主页 → 处理浮窗：步骤={}，结果=无浮窗，已处理={}',
                        step,
                        handled,
                    )
                    if navigation_context is not None and attempt is not None:
                        navigation_context.record_result(
                            HomeCheckObservation(
                                matched=True,
                                overlay_handled=handled,
                                attempt=attempt,
                            ),
                        )
                    return handled

                handled = True
                _log.debug(
                    '[UI] 主页 → 浮窗识别：步骤={}，类型={}，结果=已识别',
                    step,
                    overlay.value.kind.value if overlay.value is not None else 'unknown',
                )
                workflow.handle_overlay(
                    self._ctrl,
                    overlay,
                    record_screenshot=record_screenshot,
                )
        except ApplicationError as error:
            _log.error(
                '[UI] 主页 → 处理浮窗：结果=失败，错误类型={!r}，原因={!r}',
                type(error).__name__,
                str(error),
            )
            if navigation_context is not None:
                navigation_context.record_error(error)
            raise

        _log.error('[UI] 主页 → 处理浮窗：结果=失败，原因=流程步骤耗尽')
        raise workflow.HomeOverlayError('主页浮窗流程未在限定步骤内完成')

    # -- 导航契约 ------------------------------------------------------------

    def navigate_to(self, target: Target) -> None:
        """从主页进入一个受支持的目标页面。

        Args:
            target: 要进入的目标页面。

        Raises:
            ValueError: 目标页面不在主页导航契约中。
        """
        # 局部导入用于延迟加载依赖页面控制器的导航适配器。
        from autowsgr.application.ui.navigation.interaction import click_and_wait_for_page

        if target is Target.EVENT:
            # 活动页面拥有独立流程，延迟导入以保持页面依赖方向清晰。
            from autowsgr.application.ui.navigation.event import navigate_to_event

            _log.info('[UI] 主页 → 进入活动页面：状态=开始')
            navigate_to_event(self._ctx, max_retries=_EVENT_NAVIGATION_MAX_RETRIES)
            _log.info('[UI] 主页 → 进入活动页面：结果=成功')
            return

        # 1. 进入其他页面前先清理已知浮窗。
        if self.dismiss_current_overlay():
            time.sleep(_OVERLAY_CLEAN_DELAY_SECONDS)

        # 2. 根据目标选择页面终态检查器。
        if target is Target.SORTIE:
            # 延迟导入避免初始化主页时加载全部同层页面控制器。
            from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
                SortiePage,
            )

            checker = SortiePage.check_current_page
        elif target is Target.TASK:
            from autowsgr.application.ui.controller.operations.mission_page import MissionPage

            checker = MissionPage.check_current_page
        elif target is Target.SIDEBAR:
            from autowsgr.application.ui.controller.sidebar.main_page import SidebarPage

            checker = SidebarPage.check_current_page
        elif target is Target.BACKYARD:
            from autowsgr.application.ui.controller.backyard.main_page import BackyardPage

            checker = BackyardPage.check_current_page
        else:
            raise ValueError(f'未知的导航目标: {target}')

        coordinate = constants.NAV_POSITIONS[target.name.lower()]
        _log.info('[UI] 主页 → 进入页面：目标={}，状态=开始', target.value)
        try:
            # 3. 执行点击并确认目标页面终态。
            click_and_wait_for_page(
                self._ctrl,
                click_coord=coordinate,
                checker=checker,
                source=PageName.HOME.value,
                target=target.page_name.value,
            )
        except Exception as error:
            _log.error(
                '[UI] 主页 → 进入页面：目标={}，结果=失败，错误类型={!r}，原因={!r}',
                target.value,
                type(error).__name__,
                str(error),
            )
            raise
        _log.info('[UI] 主页 → 进入页面：目标={}，结果=成功', target.value)


__all__ = ['HomePage', 'Target']
