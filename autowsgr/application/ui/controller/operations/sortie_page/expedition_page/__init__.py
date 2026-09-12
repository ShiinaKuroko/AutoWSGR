"""模块功能：提供远征页面控制器。

上层调用：
- business.logistics.expedition：驱动远征通知检查和收取。

下层依赖：
- application.ui.controller.operations.sortie_page.expedition_page.page：提供页面行为。
- application.ui.controller.operations.sortie_page.expedition_page.constants：提供页面校准。
"""

from autowsgr.application.ui.controller.operations.sortie_page.expedition_page.page import (
    ExpeditionPage,
)


__all__ = ['ExpeditionPage']
