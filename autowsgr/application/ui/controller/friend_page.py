"""好友页面 UI 控制器。

已完成

页面入口:
    主页面 → 侧边栏 → 好友


使用方式::

    from autowsgr.application.ui.controller.friend_page import FriendPage

    page = FriendPage(ctrl)
    page.go_back()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common.calibration.friend import CLICK_BACK
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page
from autowsgr.common.vision import PageMatch


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('ui')

# ═══════════════════════════════════════════════════════════════════════════════
# 页面识别签名
# ═══════════════════════════════════════════════════════════════════════════════



# ═══════════════════════════════════════════════════════════════════════════════
# 点击坐标
# ═══════════════════════════════════════════════════════════════════════════════



# ═══════════════════════════════════════════════════════════════════════════════
# 页面控制器
# ═══════════════════════════════════════════════════════════════════════════════


class FriendPage:
    """好友页面控制器。

    Parameters
    ----------
    ctrl:
        Android 设备控制器实例。
    """

    def __init__(self, ctx: GameContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面识别 ──────────────────────────────────────────────────────────

    @staticmethod
    def is_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否为好友页面。

        通过标签页统一检测层判定 (4 标签 + 头部探测点较亮),返回带覆盖度分数的 PageMatch。

        Parameters
        ----------
        screen:
            截图 (HxWx3, RGB)。
        """
        from autowsgr.application.ui.controller.shared.tabbed_page import (
            TabbedPageType,
            check_tabbed_page,
        )

        return check_tabbed_page(screen, TabbedPageType.FRIEND)

    # ── 回退 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击回退按钮 (◁)，返回侧边栏。

        Raises
        ------
        NavigationError
            超时仍在好友页面。
        """
        from autowsgr.application.ui.controller.sidebar_page import SidebarPage

        _log.info('[UI] 好友 → 返回侧边栏')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=CLICK_BACK,
            checker=SidebarPage.is_current_page,
            source='好友',
            target=PageName.SIDEBAR,
        )
