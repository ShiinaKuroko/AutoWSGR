"""模块功能：提供战役页面控制器和识别结果。

上层调用：
- business.combat.campaign：驱动战役难度、次数和出征入口。

下层依赖：
- application.ui.controller.operations.sortie_page.campaign_page.page：提供页面行为。
- application.ui.controller.operations.sortie_page.campaign_page.constants：提供页面校准。
- application.ui.controller.operations.sortie_page.campaign_page.recognition：提供 OCR 结果和识别函数。
"""

from autowsgr.application.ui.controller.operations.sortie_page.campaign_page.page import (
    CampaignPage,
)
from autowsgr.application.ui.controller.operations.sortie_page.campaign_page.recognition import (
    AcquisitionCounts,
)


__all__ = ['AcquisitionCounts', 'CampaignPage']
