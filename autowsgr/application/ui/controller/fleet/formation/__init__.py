"""模块功能：组织编队识别、编队调整和编队选船三个核心节点。

上层调用：
- main_page.page：调用编队核心完成准备页舰队调整。

下层依赖：
- fleet_recognition、fleet_adjustment、ship_selection：提供编队核心的三个业务节点。

编队总流程入口由 workflow.py 提供，本包只导出完整编队核心的业务入口。
"""

from autowsgr.application.ui.controller.fleet.formation.workflow import (
    adjust_fleet,
    read_fleet_snapshot,
    validate_campaign_fleet,
)


__all__ = ['adjust_fleet', 'read_fleet_snapshot', 'validate_campaign_fleet']
