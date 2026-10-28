"""模块功能：提供主页检查器的模块入口。

上层调用：
- application.ui.navigation：调用主页与每日浮窗的识别入口。

下层依赖：
- home.checker：提供识别入口与浮窗事实模型。

本模块只导出稳定入口与事实模型，不放业务实现。
"""

from autowsgr.application.ui.navigation.checker.home.checker import (
    HomeNewsOverlay,
    check_home_reward_confirm,
    check_home_reward_overlay,
    check_news_checked,
    mark_popups_settled,
    popups_all_settled,
    read_home_layer,
    read_news_checkbox_center,
    read_news_overlay,
    read_reward_claim_center,
    read_reward_confirm_center,
)


__all__ = [
    'HomeNewsOverlay',
    'check_home_reward_confirm',
    'check_home_reward_overlay',
    'check_news_checked',
    'mark_popups_settled',
    'popups_all_settled',
    'read_home_layer',
    'read_news_checkbox_center',
    'read_news_overlay',
    'read_reward_claim_center',
    'read_reward_confirm_center',
]
