# 后端用户操作方式全景清单（兼容性底线）

> 整理时间：2026-08-23
> 背景：后端架构升级（统一 TaskProcessor）前，摸清所有既有用户的使用习惯，确保升级不破坏任何一条路径。
> 分析基线：AutoWSGR ShiinaKuroko 分支 @ 7ec26af

---

## 关键事实

1. **AutoWSGR v2 从来没有统一 CLI**
   - `pyproject.toml` 无 `[project.scripts]` / console_scripts
   - pip 安装后没有 `autowsgr` 命令
   - 用户的"命令行用法"实际是四种习惯（见下）
2. **官方文档（docs/usage/usage_quickstart.md）教的是 Python SDK 写法**——用户写脚本 `from autowsgr.ops import ...`，这是后端高级用户的主流形态
3. **唯一有正式 argparse 参数契约的脚本只有 2 个**：`auto_daily.py` 和 `week.py`，其余 examples 全靠"用户改代码里的常量"传参

---

## 习惯 A：直接跑 examples 脚本（最普遍）

| 脚本 | 用户敲的命令 | 参数方式 | 行为特征 |
|---|---|---|---|
| 挂机 | `python examples/auto_daily.py` | ✅ argparse：`--config <yaml>`、`--expedition-interval <秒>`、若干 `--no-xxx` 开关 | 唯一永续挂机入口，读 usersettings 的 daily_automation 段 |
| 周常 | `python examples/week.py <计划路径>` | 半参数化：sys.argv[1] 传计划路径 + last_point 条件写死在代码里 | 单次跑完退出 |
| 常规战 | `python examples/normal_fight.py` | ❌ 无参数，改代码里的 PLAN/TIMES 常量 | 单次跑完退出 |
| 活动战 | `python examples/event_fight.py` | ❌ 同上（plan名/times/fleet_id 写死） | 单次跑完退出 |
| 战役 | `python examples/campaign.py` | ❌ 同上（战役名/times 写死） | 单次跑完退出 |
| 演习 | `python examples/exercise.py` | ❌ 同上（fleet_id 写死） | 单次跑完退出 |
| 决战 | `python examples/decisive.py` | ❌ 同上（DecisiveConfig 写死） | 单次跑完退出 |
| 远征循环 | `python examples/expedition.py` | ❌ 无参死循环（while True 收远征+重派+修理） | 永续，Ctrl+C 停 |
| 换编队 | `python examples/change_fleet.py` | ❌ 同上（舰队号/舰船列表写死） | 单次跑完退出 |

**共同特征**：每个脚本自己调 `launch()` 初始化，跑完进程退出。

---

## 习惯 B：自写 Python 脚本（官方文档教的正规用法）

用户拿 examples 当模板，直接 import 后端 API：

```python
from autowsgr.emulator import ADBController
from autowsgr.ops import run_normal_fight, collect_expedition, CampaignConfig, run_campaign
from autowsgr.combat.plan import CombatPlan

ctrl = ADBController(serial="127.0.0.1:5555")
ctrl.connect()
plan = CombatPlan.from_yaml("plans/normal_fight/5-4.yaml")
results = run_normal_fight(ctrl, plan, times=5)
```

**依赖的 API 面**（升级时签名不能动）：
- `ops/` 层所有公开函数：`run_normal_fight` / `run_campaign` / `collect_expedition` / `collect_rewards` / `goto_page` / `identify_current_page` ...
- `combat/plan.py`：`CombatPlan.from_yaml()`
- `combat/callbacks.py`：`CombatResult`
- `emulator/`：`ADBController(serial=...)` + `connect()` / `screenshot()` / `click()`
- scheduler 层：`launch()` / `TaskScheduler` / `build_daily_plan()`

---

## 习惯 C：工具脚本

| 命令 | 用途 |
|---|---|
| `python tools/migrate_config.py --old <classic.yaml> --out <new.yaml> [--dry-run]` | v1 classic 配置迁移到 v2 |
| `python tools/debug_screenshot.py [--roi x,y,w,h] [--allowlist "0-9"] [-i img.png]` | OCR 调试（开发者） |
| `python tools/pixel_marker.py --serial 127.0.0.1:5555` | 像素标记调试（开发者） |

---

## 习惯 D：classic v1 老用户（上游 main 分支）

- v1 入口：`timer = start_script('settings.yaml')`（God Object 模式）
- v2 通过 `autowsgr/infra/config_compat.py` 检测 classic 配置字段并**提示运行迁移工具**，不直接兼容 v1 API
- quickstart 附录有完整 v1→v2 迁移对照表
- **结论：无需为 v1 API 做兼容**，已有独立迁移路径

---

## 兼容性底线（处理器设计必须遵守）

| 用户习惯 | 兼容底线 | 设计含义 |
|---|---|---|
| A 跑 examples | 脚本路径和调用签名不变，内部改走处理器 | examples 变成处理器的薄壳，用户零感知 |
| B SDK 自写脚本 | `ops/` 层 API 签名不变 | 处理器包在 ops 之上，不动 ops 本身 |
| C auto_daily 参数化 | argparse 签名原样保留 | 参数翻译成处理器的任务描述符 |
| D classic v1 | 已有迁移工具路径 | 不用管 |

**核心结论**：因为大部分 examples 参数靠"用户改代码"，实际不存在需要兼容的"命令行参数格式"——统一处理器的 CLI 兼容成本极低。处理器不发明新 CLI，只是把 examples 的"代码即参数"和 GUI 的"HTTP 即参数"统一翻译成同一种任务描述符。
