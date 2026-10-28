"""模块功能：提供任务页检查器的模块入口。

上层调用：
- application.ui.navigation：调用任务页、领奖按钮与确认浮窗的确认入口。

下层依赖：
- mission.checker：提供识别入口。

本模块只导出稳定入口，不放业务实现。
"""

from autowsgr.application.ui.navigation.checker.mission.checker import (
    check_claim_all_button,
    check_mission_page,
    check_mission_reward_confirm,
)


__all__ = [
    'check_claim_all_button',
    'check_mission_page',
    'check_mission_reward_confirm',
]
