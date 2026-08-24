"""游戏操作层 (GameOps) — 跨页面组合操作。

本模块提供高级游戏操作函数，每个函数封装了涉及多个页面切换的完整业务流程。

与 UI 层的区别:

- **UI 层** (:mod:`autowsgr.ui`): 单页面内的原子操作（识别、点击、状态查询）
- **GameOps 层** (:mod:`autowsgr.ops`): 跨页面导航 + 委托 UI 执行

设计原则:

- **无状态**: 所有函数都是纯函数式的，不维护全局 ``now_page``
- **薄包装**: ops 只负责导航，实际操作全部委托 UI 层
- **可组合**: 函数之间通过 ``ctrl`` 串联
- **可测试**: mock ``AndroidController`` 即可单元测试

模块结构::

    ops/
    ├── __init__.py        ← 本文件 (统一导出)
    ├── decisive/          ← 决战过程控制器
    ├── normal_fight.py    ← 常规战斗 (多节点地图)
    ├── campaign.py        ← 战役战斗 (单点)
    ├── cook.py            ← 食堂做菜
    ├── destroy.py         ← 解装舰船
    ├── build.py           ← 建造/收取
    ├── startup.py         ← 游戏启动与导航到主页面 (浮层处理已迁 business/system/initialize)
    └── image_resources.py ← 图像模板资源注册中心

    已迁移到新架构 (business/* 或 infra/*, 原 ops 入口已删除):
    navigate.py → business/system/navigate.py; exercise.py →
    business/combat/exercise.py; expedition.py → business/logistics/expedition.py;
    reward.py → business/logistics/reward.py; repair.py →
    business/logistics/repair/bath_repair.py。
"""

# ── 建造 ──
from autowsgr.ops.build import BuildRecipe, build_ship, collect_built_ships

# ── 战役 ──
from autowsgr.ops.campaign import CampaignRunner

# ── 食堂 ──
from autowsgr.ops.cook import cook

# ── 决战 ──
from autowsgr.ops.decisive import DecisiveController, DecisiveResult

# ── 解装 ──
from autowsgr.ops.destroy import destroy_ships

# ── 活动战斗 ──
from autowsgr.ops.event_fight import (
    EventFightRunner,
    run_event_fight,
    run_event_fight_from_yaml,
)

# ── 常规战斗 ──
from autowsgr.ops.normal_fight import (
    NormalFightRunner,
    run_normal_fight,
    run_normal_fight_from_yaml,
)

# ── 启动 (未迁移完, 待并入 business/system/initialize) ──
from autowsgr.ops.startup import (
    ensure_game_ready,
    go_main_page,
    is_game_running,
    is_on_main_page,
    restart_game,
    start_game,
)


__all__ = [
    # 建造
    'BuildRecipe',
    # 战役
    'CampaignRunner',
    # 决战
    'DecisiveController',
    'DecisiveResult',
    # 活动战斗
    'EventFightRunner',
    # 常规战斗
    'NormalFightRunner',
    'build_ship',
    'collect_built_ships',
    # 食堂
    'cook',
    # 解装
    'destroy_ships',
    # 启动
    'ensure_game_ready',
    'go_main_page',
    'is_game_running',
    'is_on_main_page',
    'restart_game',
    'run_event_fight',
    'run_event_fight_from_yaml',
    'run_normal_fight',
    'run_normal_fight_from_yaml',
    'start_game',
]
