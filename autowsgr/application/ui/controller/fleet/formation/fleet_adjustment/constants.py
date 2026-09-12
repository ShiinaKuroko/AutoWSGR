"""模块功能：维护编队调整流程的重试和页面同步参数。

上层调用：
- fleet_adjustment.workflow、alignment、campaign、decisive：控制有限调整和页面同步节奏。

下层依赖：
- 无。

本文件只保存编队调整跨实现共享的流程参数，不保存运行时状态。
"""

from __future__ import annotations


# ── 编队调整流程参数 ─────────────────────────────────────────────────────────

MAX_SET_RETRIES = 2  # 编队最终校验失败后允许的局部修正次数。
FLEET_SWITCH_WAIT = 0.5  # 切换准备页舰队后等待舰船卡片刷新的时间。
ACTION_WAIT = 0.3  # 单次换船或清空动作后等待准备页同步的时间。
RETRY_WAIT = 0.5  # 一轮编队校验失败后等待下一次截图的时间。
REORDER_WAIT = 0.5  # 一次拖拽排序后等待槽位顺序稳定的时间。


__all__ = ['ACTION_WAIT', 'FLEET_SWITCH_WAIT', 'MAX_SET_RETRIES', 'REORDER_WAIT', 'RETRY_WAIT']
