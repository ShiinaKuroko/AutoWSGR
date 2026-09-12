"""模块功能：维护战役面板的入口、难度和 OCR 区域常量。

上层调用：
- application.ui.controller.operations.sortie_page.campaign_page.page：读取战役页面校准。
- application.ui.controller.operations.sortie_page.campaign_page.recognition：读取战役次数区域。

下层依赖：
- 无。

本模块只保存战役页面的静态校准数据，不保存页面状态、设备对象或业务规则。
"""

from __future__ import annotations


# ── 战役入口和难度 ──────────────────────────────────────────────────────────

CAMPAIGN_POSITIONS = {
    1: (0.1704, 0.5000),  # 第 1 个战役入口，用于选择航母战役。
    2: (0.3399, 0.5000),  # 第 2 个战役入口，用于选择潜艇战役。
    3: (0.5102, 0.5000),  # 第 3 个战役入口，用于选择驱逐战役。
    4: (0.6797, 0.5000),  # 第 4 个战役入口，用于选择巡洋战役。
    5: (0.8500, 0.5000),  # 第 5 个战役入口，用于选择战列战役。
}
CLICK_DIFFICULTY = (0.8000, 0.1306)  # 战役难度按钮，用于切换简单/困难。
DIFFICULTY_EASY_COLOR = (29, 139, 234)  # 困难状态切换图标颜色，用于识别当前困难状态。
DIFFICULTY_EASY_TOLERANCE: float = 50.0  # 困难状态颜色容差，用于兼容截图渲染差异。
DIFFICULTY_HARD_COLOR = (141, 46, 52)  # 简单状态切换图标颜色，用于识别当前简单状态。
DIFFICULTY_HARD_TOLERANCE: float = 50.0  # 简单状态颜色容差，用于兼容截图渲染差异。


# ── 次数 OCR 区域 ──────────────────────────────────────────────────────────

CAMPAIGN_REMAIN_CROP = (0.0800, 0.8200, 0.2500, 0.9200)  # 战役次数 OCR 区域，用于读取剩余次数。


__all__ = [
    'CAMPAIGN_POSITIONS',
    'CAMPAIGN_REMAIN_CROP',
    'CLICK_DIFFICULTY',
    'DIFFICULTY_EASY_COLOR',
    'DIFFICULTY_EASY_TOLERANCE',
    'DIFFICULTY_HARD_COLOR',
    'DIFFICULTY_HARD_TOLERANCE',
]
