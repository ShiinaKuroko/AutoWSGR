"""模块功能：导出战役页面控制器。

上层调用：
- business.combat.campaign：调用战役出征入口。

下层依赖：
- application.ui.controller.operations.sortie_page.campaign_page.page：提供页面控制器。

边界：
只导出稳定的页面入口，不导出识别实现或页面内部步骤。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.operations.sortie_page.campaign_page.page import (
    CampaignPage,
)


__all__ = [
    'CampaignPage',
]
