"""模块功能：维护快速维修流程的同步和重试参数。

上层调用：
- repair.workflow：控制快速维修点击和有限复查。

下层依赖：
- 无。
"""

from __future__ import annotations


# ── 快速维修流程参数 ─────────────────────────────────────────────────────────

REPAIR_PANEL_WAIT = 0.8  # 打开快速维修面板后等待内容稳定的时间。
REPAIR_SLOT_WAIT = 1.5  # 每次维修点击后等待修理结果刷新的时间。
REPAIR_RETRY_COUNT = 3  # 自动维修复查失败时允许的默认重试次数。


__all__ = ['REPAIR_PANEL_WAIT', 'REPAIR_RETRY_COUNT', 'REPAIR_SLOT_WAIT']
