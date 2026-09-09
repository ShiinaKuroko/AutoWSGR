"""模块功能：从地图决战面板进入决战总览页面。

上层调用：
- application.ui.controller.operations.sortie_page.battle_page.page：组合决战面板能力。
- business.combat.decisive：启动决战流程。

下层依赖：
- application.ui.controller.operations.sortie_page.battle_page.base：提供地图面板切换。
- application.ui.controller.operations.sortie_page.battle_page.constants：提供决战入口坐标。
- application.ui.controller.operations.sortie_page.decisive_page.page：确认决战总览页到达。
"""

from __future__ import annotations

import time

from autowsgr.application.ui.controller.operations.sortie_page.battle_page.base import BaseMapPage
from autowsgr.application.ui.controller.operations.sortie_page.battle_page.constants import (
    CLICK_ENTER_DECISIVE,
)
from autowsgr.application.ui.controller.operations.sortie_page.battle_page.data import MapPanel
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page


_log = get_logger('ui')


class DecisivePanelMixin(BaseMapPage):
    """Mixin: 决战面板操作 — 进入决战。"""

    def enter_decisive(self) -> None:
        """从地图页进入决战总览页。

        Raises
        ------
        NavigationError
            超时未到达决战页面。
        """
        from autowsgr.application.ui.controller.operations.sortie_page.decisive_page.page import (
            DecisiveBattlePage,
        )

        _log.info('[UI] 地图页面 → 决战页面')

        # 0. 等待一下，确保地图页面加载完成
        time.sleep(0.5)

        # 1. 确保在决战面板
        self.ensure_panel(MapPanel.DECISIVE)
        time.sleep(0.5)

        # 2. 点击进入
        click_and_wait_for_page(
            self._ctrl,
            click_coord=CLICK_ENTER_DECISIVE,
            checker=DecisiveBattlePage.check_current_page,
            source='地图-决战面板',
            target=PageName.DECISIVE_BATTLE,
        )
