"""模块功能：导出准备页损伤识别和维修流程。

上层调用：
- main_page.page：在准备页主流程中执行快速维修。
- business.combat：提供维修策略并处理手动维修中断。

下层依赖：
- repair.workflow：编排维修检测、点击、复查和失败终态。
- repair.recognition：识别舰船损伤状态。
"""

from autowsgr.application.ui.controller.fleet.support.repair.workflow import (
    RepairStrategy,
    apply_repair,
    check_repair,
    open_quick_repair,
    repair_slots,
)


__all__ = ['RepairStrategy', 'apply_repair', 'check_repair', 'open_quick_repair', 'repair_slots']
