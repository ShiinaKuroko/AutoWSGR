"""每日弹窗处理 — 独立模块 (从旧 ops/startup.py 与 ui/main_page/overlays.py 迁移)。

业务定义 (保持原逻辑):
    每日 0 点后第一次回到首页时出现弹窗 (新闻公告 → 每日签到 → 活动预约),
    处理一次后当天零开销跳过 (日期门控)。

复用清单 (不重写):
    - ui/main_page/overlays.detect_overlay / dismiss_overlay — 浮层检测与消除
    - ui/utils.confirm_operation — 确认弹窗兜底
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from autowsgr.infra.base.ui.pages.main_page.overlays import (
    detect_overlay,
    dismiss_overlay,
)
from autowsgr.infra.logger import get_logger
from autowsgr.ui.utils import confirm_operation


if TYPE_CHECKING:
    from autowsgr.emulator import AndroidController


_log = get_logger('business.overlays')

# ═══════════════════════════════════════════════════════════════════════════════
# 常量 (沿用旧值)
# ═══════════════════════════════════════════════════════════════════════════════

_OVERLAY_DISMISS_MAX = 5
"""每日浮层消除的最大尝试次数 (新闻 → 签到 → 确认 → 二次确认 → 兜底)。"""

_OVERLAY_DISMISS_WAIT = 1.5
"""消除每个浮层后的等待时间 (秒) — 弹窗按顺序逐个出现, 需要间隔等待。"""

_OVERLAY_CONFIRM_TIMEOUT = 3.0
"""确认弹窗兜底的最大等待时限 (秒)。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 状态
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class OverlayState:
    """每日浮层的日期门控状态 — 任务级, 挂在任务上下文上, 任务结束作废。"""

    last_handled: date | None = None
    """最近一次处理浮层的日期; 与今天相同则零开销跳过。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════════════════


def handle_daily_overlays(ctrl: AndroidController, state: OverlayState) -> None:
    """每日首次回首页的浮层处理 (日期门控: 当天已处理则零开销返回)。

    流程 (与旧逻辑一致):
        ① 已知浮层 (新闻/签到/预约/提督信息) → 检测并消除
        ② 确认弹窗兜底 (检测不到浮层签名但有「确认」按钮) → 点掉
        ③ 既无浮层又无确认按钮 → 画面干净, 结束

    先标记再执行: 即使本次消除中途失败, 当天也不会反复重试
    (避免异常画面导致死循环)。
    """
    today = date.today()  # noqa: DTZ011 — 游戏按本地墙上时钟 0 点刷新
    if state.last_handled == today:
        return
    # 先标记: 当天内幂等
    state.last_handled = today

    for attempt in range(_OVERLAY_DISMISS_MAX):
        # ① 已知浮层直接消除
        screen = ctrl.screenshot()
        overlay = detect_overlay(screen)
        if overlay is not None:
            _log.info(
                '[Overlays] 消除浮层: {} ({}/{})',
                overlay, attempt + 1, _OVERLAY_DISMISS_MAX,
            )
            dismiss_overlay(ctrl, overlay)
            time.sleep(_OVERLAY_DISMISS_WAIT)
            continue

        # ② 确认弹窗兜底 (如签到奖励确认、二次确认)
        if confirm_operation(ctrl, must_confirm=False, timeout=_OVERLAY_CONFIRM_TIMEOUT):
            _log.info(
                '[Overlays] 确认弹窗兜底 ({}/{})',
                attempt + 1, _OVERLAY_DISMISS_MAX,
            )
            time.sleep(_OVERLAY_DISMISS_WAIT)
            continue

        # ③ 画面干净, 流程完成
        return
