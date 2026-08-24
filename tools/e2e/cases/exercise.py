"""演习断点打断 E2E — 处理器暂停 + 远征检查插入 + 重跑计数。

验证用户敲定的五个场景 (一次运行验证一个断点场景, 演习对手打完即无):
    1. --pause-at panel_ready      导航结束后暂停 → 插远征检查 → 回主页
    2. --pause-at rival_confirmed  确认对手后暂停 → 插远征检查 → 回主页
    3. --pause-at fleet_ready      编队完成后暂停 → 插远征检查 → 回主页
    4. --pause-at rival_done       战斗完成后暂停 (计数保留) → 插远征检查 → 回主页
    5. 不带 --pause-at              直接跑完并统计计数

接力模式 (--relay, 2026-08-25 用户敲定的六段实机流程):
    同一趟演习里依次在四个断点各插入一次远征检查 (导航结束 → 选对手结束 →
    编队确认 → 打一场), 每次打断后自动恢复, 直到打完收尾; 配合 --with-init
    在演习前先跑初始化链路 (含每日浮层清理)。

核心语义 (2026-08 用户敲定): 一次提交 = 持续打到没有对手 (以「打一个」
为基础单元循环); 每打完一个对手计数 +1; 中间被更高优先级任务打断时在断点
暂停 → 高优任务执行 → 恢复后接着打剩余的 → 直到没有对手。

打断机制: 事件回调里收到目标事件 → processor.interrupt(远征检查请求)
→ 演习执行器在最近的 _wait 断点回主页、抛 TaskPaused → 处理器清信号、
重排队 → 远征检查先跑 → 演习重跑 (已打对手变灰自动跳过, 计数保留)。

用法::

    # 场景4: 打完一个对手后打断一次
    python tools/e2e/run.py --with-ocr exercise --pause-at rival_done

    # 场景5: 不打断, 跑完全部并统计
    python tools/e2e/run.py --with-ocr exercise

    # 六段接力: 初始化(清弹窗) → 演习四断点各插一次远征检查 → 打完
    python tools/e2e/run.py --with-ocr exercise --relay --with-init

    # 换计划 YAML
    python tools/e2e/run.py --with-ocr exercise --yaml <路径>
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import argparse

DESC = '演习: 断点打断 + 远征检查插入 + 重跑计数 (需 --with-ocr)'

# 默认计划: GUI 系统预设的队伍2演习 (用户提供的驱动 YAML)
_DEFAULT_YAML = (
    r'c:\ShiinaKuroko\01.Project\AutoWSGR-GUI'
    r'\resource\system_daily_plans\exercise-队伍2演习.yaml'
)

# 四个断点事件 (与 exercise.py 的上报一一对应)
_BREAKPOINTS = ('panel_ready', 'rival_confirmed', 'fleet_ready', 'rival_done')

# 接力模式的打断顺序: 每个断点各打断一次, 打断点必须在事件流中依次出现
_RELAY_PAUSES = ('panel_ready', 'rival_confirmed', 'fleet_ready', 'rival_done')


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """定义 case 专属命令行参数。"""
    parser.add_argument('--yaml', default=_DEFAULT_YAML, help='演习计划 YAML 路径')
    parser.add_argument(
        '--pause-at',
        choices=_BREAKPOINTS,
        default=None,
        help='在哪个断点触发处理器打断 (不指定 = 不打断直接跑完)',
    )
    parser.add_argument(
        '--relay',
        action='store_true',
        help='接力模式: 四个断点 (导航→选对手→编队→打一场) 依次各打断一次',
    )
    parser.add_argument(
        '--with-init',
        action='store_true',
        help='演习前先跑初始化链路 (任意状态 → 首页 + 每日浮层清理)',
    )


def run(rt: Any) -> bool:
    """执行演习断点打断验证 (单断点 / 接力 / 可带初始化前置)。"""
    from autowsgr.business.system.navigate import identify_current_page
    from autowsgr.dispatch.processor import Processor, Request
    from autowsgr.types import PageName

    args = rt.args
    ctx = rt.ctx
    rt.note(f'计划: {args.yaml}')
    if args.relay:
        rt.note(f'模式: 接力 ({">".join(_RELAY_PAUSES)})')
    else:
        rt.note(f'打断点: {args.pause_at or "(不打断, 场景5)"}')

    # ── 阶段零 (可选): 初始化链路 + 每日浮层清理 ────────────────
    if args.with_init:
        from autowsgr.business.system.initialize.initialize import initialize
        from autowsgr.infra.base.ui.pages.main_page import MainPage
        from autowsgr.infra.base.ui.pages.main_page.overlays import detect_overlay

        if rt.action('初始化 (任意状态 → 首页 + 清浮层)', initialize, ctx) is rt.FAILED:
            return False
        rt.check('初始化后: 主页面基础态', MainPage.is_base_page, ctx.ctrl.screenshot())
        rt.check(
            '初始化后: 无浮层残留',
            lambda: detect_overlay(ctx.ctrl.screenshot()) is None,
        )

    # ── 准备: 演习请求 (YAML 驱动) + 处理器 ─────────────────────
    exercise_req = rt.action('加载演习计划 YAML', Request.from_yaml, args.yaml, source='cli')
    if exercise_req is rt.FAILED:
        return False
    rt.note(f'task_type={exercise_req.task_type} params={exercise_req.params} → 持续打到没有对手')

    processor = Processor(ctx)
    events: list[tuple[str, dict]] = []  # 事件流水 (供断言与人工核对)
    snapshots: dict[str, Any] = {}  # 关键时刻的状态快照
    # 接力模式: 当前断点队列下标 + 各断点是否已触发 (重跑会重复上报事件)
    relay_index = [0]
    relay_fired: list[bool] = [False] * len(_RELAY_PAUSES)

    def interrupt_now(event: str) -> None:
        """在断点插入远征检查 (处理器加急)。"""
        rt.note(f'>> 断点 [{event}] 触发处理器加急: 插入远征检查')
        processor.interrupt(Request(task_type='expedition_check', source='dependency'))

    def on_event(event: str, **data: Any) -> None:
        events.append((event, dict(data)))
        if event == 'paused':
            # paused 上报发生在回主页之后 → 立即验证锚点铁律
            page = identify_current_page(ctx)
            fought = exercise_req.progress.get('fought', 0)
            if args.relay:
                snapshots.setdefault('paused_pages', []).append(page)
                snapshots.setdefault('paused_fought', []).append(fought)
            else:
                snapshots['paused_page'] = page
                snapshots['paused_fought'] = fought
        if args.relay:
            # 依次消费断点队列: 每个断点只在第一次上报时触发
            idx = relay_index[0]
            if idx < len(_RELAY_PAUSES) and event == _RELAY_PAUSES[idx] and not relay_fired[idx]:
                relay_fired[idx] = True
                relay_index[0] = idx + 1
                interrupt_now(event)
        elif event == args.pause_at and not snapshots.get('interrupted'):
            # 到达目标断点 → 模拟下游依赖加急插入远征检查
            snapshots['interrupted'] = True
            interrupt_now(event)

    processor.on_event = on_event

    # ── 阶段一: 首次提交 (可能被断点打断后恢复) ──────────────────
    processor.submit(exercise_req)
    outcomes = rt.action('首次提交 (演习 + 可能的打断恢复)', processor.run_pending)
    if outcomes is rt.FAILED:
        return False

    status_flow = [(status, req.task_type) for status, req, _ in outcomes]
    rt.note(f'执行流: {status_flow}')
    rt.note(f'事件流水: {[e for e, _ in events]}')

    if args.relay:
        # 接力模式: 演习暂停×4 → 远征检查×4 → 演习重跑完成
        expected_flow: list[tuple[str, str]] = []
        for _ in _RELAY_PAUSES:
            expected_flow += [('paused', 'exercise'), ('done', 'expedition_check')]
        expected_flow.append(('done', 'exercise'))
        rt.check('执行流 = (暂停→远征检查)×4 → 重跑完成', lambda: status_flow == expected_flow)
        rt.check('四个断点全部触发过', lambda: all(relay_fired))
        paused_pages = snapshots.get('paused_pages', [])
        rt.check(
            '每次打断都在主页面 (锚点铁律)',
            lambda: len(paused_pages) == len(_RELAY_PAUSES)
            and all(page == PageName.MAIN for page in paused_pages),
        )
    elif args.pause_at:
        # 打断场景: 演习暂停 → 远征检查先跑 → 演习重跑完成
        rt.check(
            '执行流 = 暂停 → 远征检查 → 重跑完成',
            lambda: status_flow
            == [('paused', 'exercise'), ('done', 'expedition_check'), ('done', 'exercise')],
        )
        rt.check('打断时已回到主页面 (锚点铁律)', lambda: snapshots.get('paused_page') == PageName.MAIN)
        rt.check(f'打断点 [{args.pause_at}] 确实触发过', lambda: bool(snapshots.get('interrupted')))
        if args.pause_at == 'rival_done':
            # 战斗完成后打断: 计数已保留 (打过的那一场不丢)
            rt.check('打断时计数已保留 (fought >= 1)', lambda: snapshots.get('paused_fought', 0) >= 1)
    else:
        # 场景5: 不打断, 一趟完成
        rt.check('执行流 = 单趟完成', lambda: status_flow == [('done', 'exercise')])

    # ── 计数统计: 一次提交打光全部 (rival_done 逐场累计) ─────────
    done_results = next(
        (r for s, req, r in outcomes if s == 'done' and req.task_type == 'exercise'),
        [],
    )
    total = exercise_req.progress.get('fought', 0)
    # 最后一次打断时的保留计数 (接力 = 打一场后; 单断点 = 该断点时刻; 无打断 = 0)
    paused_fought = (
        snapshots.get('paused_fought', [0])[-1]
        if args.relay
        else snapshots.get('paused_fought', 0)
    )
    rt.note(
        f'计数统计: 本任务共打 {total} 场 '
        f'(打断时已保留 {paused_fought} 场, 重跑补打 {len(done_results)} 场)',
    )
    if total == 0:
        # 无可挑战对手 (今日该时段已打完) — 空完成本身是正确行为, 不算失败
        rt.note('无可挑战对手 (今日该时段已打完), 空完成收尾属正常')
    else:
        rt.check('每场战斗都有 rival_done 计数 (一场一计)', lambda: len(done_results) == total - paused_fought)
    rt.check('累计计数 = 暂停保留 + 重跑场数', lambda: total == paused_fought + len(done_results))

    # 远征检查执行过 (打断场景) 且终态回主页
    if args.relay or args.pause_at:
        expected_checks = len(_RELAY_PAUSES) if args.relay else 1
        rt.check(
            f'远征检查执行了 {expected_checks} 次',
            lambda: sum(1 for _, req, _ in outcomes if req.task_type == 'expedition_check')
            == expected_checks,
        )
    rt.check('终态: 主页面', lambda: identify_current_page(ctx) == PageName.MAIN)

    return rt.state.failed == 0
