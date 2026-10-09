"""模块功能：提供主页检查器的模块入口。

上层调用：
- application.ui.navigation：调用主页与每日浮窗的识别入口。

下层依赖：
- home_checker.checker：提供识别入口与浮窗事实模型。

本模块只导出稳定入口与事实模型，不放业务实现。
"""

from __future__ import annotations

from autowsgr.application.ui.navigation.page_checker.home_checker.checker import (
    HomeNewsOverlay,
    check_home_news_overlay,
    check_home_page,
    check_home_reward_confirm,
    check_home_reward_overlay,
)


__all__ = [
    'HomeNewsOverlay',
    'check_home_news_overlay',
    'check_home_page',
    'check_home_reward_confirm',
    'check_home_reward_overlay',
]
