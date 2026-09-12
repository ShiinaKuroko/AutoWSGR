"""模块功能：导出自动补给和快速补给流程。

上层调用：
- main_page.page：在编队调整后执行补给。

下层依赖：
- supply.workflow：编排补给动作。
- supply.recognition：识别自动补给状态。
"""

from autowsgr.application.ui.controller.fleet.support.supply.workflow import (
    apply_supply,
    open_quick_supply,
    supply,
    switch_auto_supply,
)


__all__ = ['apply_supply', 'open_quick_supply', 'supply', 'switch_auto_supply']
