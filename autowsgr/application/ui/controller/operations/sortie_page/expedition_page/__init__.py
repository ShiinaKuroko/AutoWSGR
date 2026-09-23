"""模块功能：提供远征页面控制器及其稳定业务入口。

上层调用：
- business.logistics.expedition：驱动远征通知检查和收取。

下层依赖：
- application.ui.controller.operations.sortie_page.expedition_page.page：提供页面行为。

本模块只导出页面控制器，不执行页面操作、识别或流程调度。
"""

from autowsgr.application.ui.controller.operations.sortie_page.expedition_page.page import (
    ExpeditionPage,
)


__all__ = ['ExpeditionPage']
