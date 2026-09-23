"""模块功能：负责好友页面检查和返回侧边栏。

上层调用：
- application.ui.navigation.graph.logistics：执行好友页面返回侧边栏的页面边动作。
- application.ui.navigation.registry：注册好友页面检查器。
- testing.ui：执行好友页面导航验证。

下层依赖：
- application.ui.controller.sidebar.friend_page.constants：提供好友页面返回坐标。
- application.ui.controller.sidebar.friend_page.recognition：提供好友页面识别结果。
- application.ui.controller.sidebar.main_page：提供侧边栏页面检查器。
- common.device.interaction：等待侧边栏页面到达。
- common.types：提供页面名称和匹配结果类型。

边界：
只编排好友页面检查和返回侧边栏，不负责好友业务操作或跨页面导航调度。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.sidebar.friend_page import constants, recognition
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.interaction import click_and_wait_for_page


if TYPE_CHECKING:
    import numpy

    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.application.ui.navigation.types import PageMatch


_log = get_logger('ui.sidebar.friend_page')


# TODO(friend_page): 当前仅保留页面框架；好友功能开发后补充业务流程、页面操作和专项测试。


class FriendPage:
    """好友页面内的 UI 操作控制器。"""

    def __init__(self, ctx: UIContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面检查 ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: numpy.ndarray) -> PageMatch:
        """检查截图是否属于好友页面。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            好友页面匹配结果。
        """
        return recognition.check_current_page(screen)

    # ── 页面返回 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击返回按钮并确认回到侧边栏。

        Raises:
            NavigationError: 点击后未在限定时间内回到侧边栏。
        """
        # 侧边栏页面会反向引用好友页面，局部导入用于避免页面包初始化循环。
        from autowsgr.application.ui.controller.sidebar.main_page import SidebarPage

        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=SidebarPage.check_current_page,
            source='好友',
            target=PageName.SIDEBAR.value,
        )
        _log.info('[UI] 好友 → 返回：目标={!r}，结果=成功', PageName.SIDEBAR.value)
