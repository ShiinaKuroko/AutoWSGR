"""初始化链路 E2E — dispatch.startup.ensure_ready 实机验证。

验证终态契约: 任意状态 → [首页 + 浮层已清 + 待机]。
配合 ``--no-launch`` 使用 (跳过框架自己的 ensure_ready, 让本 case 全权处理):
- 默认: 游戏保持当前状态, 验证分支 1/2 (已在首页 / 游戏内导航回首页)
- ``--cold``: 先强杀游戏, 验证完整冷启动分支 3 (启动 → 进入 → 首页 → 清浮层)

用法::

    python tools/debug_toolkit/main.py e2e --no-launch initialize
    python tools/debug_toolkit/main.py e2e --no-launch initialize --cold
"""

from __future__ import annotations

import time
from typing import Any


DESC = '初始化链路: 任意状态 → 首页待机 (SL 兜底)'


def add_arguments(parser: Any) -> None:
    """case 专属参数。"""
    parser.add_argument('--cold', action='store_true', help='先强杀游戏再初始化 (测冷启动分支)')


def run(rt: Any) -> bool:
    """执行初始化链路并验证终态契约。"""
    from autowsgr.application.ui.navigation.page_checker import home_checker
    from autowsgr.dispatch.startup import ensure_ready

    ctx = rt.ctx
    ctrl = ctx.runtime.ctrl

    # ① 初始状态记录 (对照用, 不参与判定)
    rt.note(f'初始是否在主页: {home_checker.check_home_page(ctx)}')

    # ② --cold: 强杀游戏 → 强制走冷启动分支
    if rt.args.cold:
        package = ctx.runtime.config.account.package_name
        if rt.action(f'强杀游戏 ({package})', ctrl.stop_app, package) is rt.FAILED:
            return False
        time.sleep(2.0)

    # ③ 主体: ensure_ready (内部含三分支判定 + SL 兜底)
    if rt.action('执行 ensure_ready', ensure_ready, ctx) is rt.FAILED:
        return False

    # ④ 终态契约验证: 首页 + 浮层已清
    rt.check('终态: 在主页', lambda: home_checker.check_home_page(ctx))
    rt.check('终态: 公告浮窗已清', lambda: not home_checker.check_home_news_overlay(ctx).matched)
    rt.check('终态: 奖励浮窗已清', lambda: not home_checker.check_home_reward_overlay(ctx))
    return rt.state.failed == 0
