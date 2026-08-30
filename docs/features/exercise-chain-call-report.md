# 演习链路调用报告

日期：2026-08-30  
仓库：`C:\ShiinaKuroko\01.Project\.worktrees\20260830-exercise-team-contract-4c71\AutoWSGR`  
基线提交：`a1338a9 refactor(infra): split combat foundations`

## 结论

演习主链路已经按新的单向依赖运行到编队选船阶段：

```text
E2E / HTTP / CLI
  -> Processor
  -> ExerciseExecutor
  -> ExerciseOperations
  -> Navigator / UI pages
  -> FleetChange + OCR
  -> CombatEngine
```

本次基建改动符合预期的部分：

- 演习业务入口位于 `autowsgr/business/combat/exercise/`。
- 战斗驱动位于 `autowsgr/infra/combat/engine/`。
- 动作、阶段处理、识别、记录和规则位于 `autowsgr/infra/combat/` 的并列模块。
- 编队规则位于 `autowsgr/infra/fleet/`。
- 页面导航、页面控制器、校准坐标、视觉和设备能力位于 `autowsgr/infra/`。
- 演习业务没有直接导入旧 `autowsgr.combat`、旧 `autowsgr.vision` 或旧 `autowsgr.emulator`。

## 入口与调度

| 节点 | 文件与行号 | 作用 |
| --- | --- | --- |
| E2E 提交 | `tools/e2e/cases/exercise.py:180-224` | 初始化、加载 YAML、创建 Processor、注册断点回调 |
| HTTP 演习入口 | `autowsgr/server/routes/task.py:388-399` | 将请求交给 Processor |
| 请求解析 | `autowsgr/dispatch/processor.py:96-203` | YAML 快照、任务类型和参数准入 |
| 提交/运行 | `autowsgr/dispatch/processor.py:228-436` | 入队、优先级、暂停恢复和 Executor 调用 |
| 执行器注册 | `autowsgr/dispatch/registry.py:20-63` | 延迟导入 `business.combat.exercise` 并构造 `ExerciseExecutor` |

## 演习业务链

| 步骤 | 文件与行号 | 调用 |
| --- | --- | --- |
| 任务初始化 | `autowsgr/business/combat/exercise/executor.py:78-103` | 初始化到首页，创建演习面板循环 |
| 进入演习 | `autowsgr/business/combat/exercise/operations.py:40-45` | `goto_page(MAIN)` → `goto_page(MAP)` → 切换 `EXERCISE` 面板 |
| 选择对手 | `operations.py:46-60` | 读取 `MapPage.get_exercise_rival_status()` 并选择最上方可挑战对手 |
| 进入准备页 | `operations.py:58-60` | 对手预览页点击挑战，进入 `BattlePreparationPage` |
| 编队 | `operations.py:62-92` | 选择队伍，调用 `BattlePreparationPage.change_fleet()` |
| 准备 | `operations.py:94-105` | 自动补给、快速维修和战前血量识别 |
| 出征 | `operations.py:107-111` | 点击出征并上报 `battle_started` |
| 战斗 | `autowsgr/business/combat/exercise/executor.py:160-168` | 调用 `autowsgr.infra.combat.run_combat()` |
| 收尾 | `executor.py:113-118` | 战斗结果计数、继续演习或返回首页 |

## 导航链

| 能力 | 文件与行号 | 作用 |
| --- | --- | --- |
| 语义导航入口 | `autowsgr/infra/ui/navigation/service.py:40-183` | 识别当前页、按图寻路、栈对账、回退重试 |
| 导航图 | `autowsgr/infra/ui/navigation/graph.py:69-231` | `MAIN ↔ MAP`、`BATTLE_PREP → MAP` 等安全边 |
| 页面注册 | `autowsgr/infra/ui/navigation/registry.py:77-114` | 懒加载并注册新 UI 页面 |
| 地图页面 | `autowsgr/infra/ui/pages/map/page.py:21-35` | 组合出征、演习、远征等 panel |
| 演习面板 | `autowsgr/infra/ui/pages/map/panels/exercise.py:84-248` | 对手状态、滚动、挑战和准备页跳转 |
| 出征准备 | `autowsgr/infra/ui/pages/battle_preparation/base.py:167-201` | 回地图、出征、选队伍、槽位访问 |

## 编队与 OCR 链

```text
ExerciseOperations.configure_fleet
  -> BattlePreparationPage.change_fleet
  -> FleetChangeMixin.change_fleet
  -> FleetDetectMixin.detect_fleet_snapshot
  -> FleetPlanningMixin._plan_target_options
  -> FleetSelectionMixin._try_select_option
  -> ChooseShipPage.change_single_ship
  -> locate_ship_rows / ApiDll / FastOCR
```

关键文件：

- `autowsgr/infra/ui/pages/battle_preparation/fleet_change/_change.py:390-537`
- `autowsgr/infra/ui/pages/battle_preparation/fleet_change/_detect.py:263-315`
- `autowsgr/infra/ui/pages/battle_preparation/fleet_change/_planning.py:33-70`
- `autowsgr/infra/ui/pages/battle_preparation/fleet_change/_selection.py:67-90`
- `autowsgr/infra/ui/pages/choose_ship.py:205-496`
- `autowsgr/infra/ui/ship_list.py:105-206`
- `autowsgr/infra/vision/ocr.py:425-600`
- `autowsgr/infra/fleet/model.py:147-453`

## 战斗基建链

| 子系统 | 文件 | 责任 |
| --- | --- | --- |
| 驱动 | `autowsgr/infra/combat/engine/engine.py:38-181` | 战斗状态机循环和终态结果 |
| 状态/计划 | `autowsgr/infra/combat/engine/state.py`、`plan.py` | 阶段转移、模式和节点策略 |
| 阶段处理 | `autowsgr/infra/combat/handlers.py:75-655` | 阶段决策、观测采集和结果记录 |
| 动作 | `autowsgr/infra/combat/actions.py:38-169` | 点击、加速、弹窗确认等物理动作 |
| 阶段识别 | `autowsgr/infra/combat/recognizer.py:204-393` | 模板/像素轮询和停止查询 |
| 领域识别 | `autowsgr/infra/combat/recognition.py:108-419` | 敌舰、阵型、战果、掉落和血量识别 |
| 记录 | `autowsgr/infra/combat/history.py` | `CombatEvent`、`CombatResult`、战果历史 |
| 节点 | `autowsgr/infra/combat/node_tracker.py` | 常规/活动地图节点追踪 |
| 规则 | `autowsgr/infra/combat/rules.py` | 敌方规则和血量前进条件 |

业务层只从 `autowsgr.infra.combat` 导入公开入口；坐标通过
`autowsgr/infra/data/calibration/coordinates/combat.yaml` 加载。

## 五个实机断点映射

| 用户断点 | 代码节点 | 本次实机 |
| --- | --- | --- |
| 导航到演习入口 | `executor.py:98-99`，事件 `panel_ready` | 已触发 |
| 进入编队页面 | `executor.py:109-111`，事件 `formation_entered` | 已触发 |
| 一次选船结束 | `fleet_change/_change.py` 回调 `ship_selected` | 已触发 |
| 点击出征前 | `executor.py:121-125`，事件 `before_start` | 未到达，前置编队失败 |
| 战斗结束后 | `executor.py:128-135`，事件 `rival_done` | 未到达，未进入战斗 |

暂停控制由 `BaseExecutor._wait()` 和 `Processor.interrupt()` 共同完成；战斗动画本身是
原子段，战斗中只检查停止请求，不响应暂停，请求在战斗结束后的安全断点交接。

## 残留风险

这些不是本次演习主链路的新依赖，但仍需后续迁移：

1. `autowsgr/infra/ui/navigation/graph.py` 的后院、侧边栏、活动和决战边仍动态导入旧 `autowsgr.ui`。
2. `autowsgr/infra/ui/pages/map/panels/decisive.py` 等旧页面边界尚未迁完。
3. `autowsgr/infra/ui/pages/battle_preparation/repair.py` 仍转调 `business/logistics/repair/quick_repair.py`，存在跨层反向依赖。
4. `autowsgr/infra/runtime/context/game_context.py` 仍是混合状态容器，尚未完全拆成 RuntimeSession 和领域状态。
5. `autowsgr/scheduler/daily_plan.py` 的旧 `auto_exercise` 路径仍引用 `ExerciseOnceRunner`，属于旧调度资产。
6. `CHOOSE_SHIP` 不是导航图节点，当前由准备页编队能力直接控制，后续需要补齐语义节点或明确继续保持中转页。

这些残留没有被复制进新的演习 Executor，也没有改变本次已验证的 `business → infra` 方向。
