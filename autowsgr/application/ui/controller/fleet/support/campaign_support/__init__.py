"""模块功能：导出战役支援状态和开关流程。

上层调用：
- main_page.page、application.combat：在需要战役支援时调用支援流程。

下层依赖：
- campaign_support.workflow：编排目标状态确认和切换。
- campaign_support.recognition：识别支援开关状态。
"""

from autowsgr.application.ui.controller.fleet.support.campaign_support.recognition import (
    SupportStatus,
    check_support_enabled,
    read_support_status,
)
from autowsgr.application.ui.controller.fleet.support.campaign_support.workflow import (
    apply_campaign_support,
    switch_campaign_support,
)


__all__ = [
    'SupportStatus',
    'apply_campaign_support',
    'check_support_enabled',
    'read_support_status',
    'switch_campaign_support',
]
