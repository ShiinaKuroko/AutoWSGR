# ShiinaKuroko 分支功能移植台账

主任务：`20260830-autowsgr-upgrade`

日期：2026-09-09

源仓库：`C:\ShiinaKuroko\01.Project\AutoWSGR`

源分支：`ShiinaKuroko`

目标分支：`codex/20260830-autowsgr-upgrade`

## 使用规则

- 只按业务语义移植，不 cherry-pick、不直接 merge、不覆盖目标 worktree。
- 每条记录必须包含源 commit、业务目的、源调用链、目标架构位置、冲突处理和验证证据。
- 合并提交只作为来源时间线标记；真正移植以其中的有效功能提交为准。
- 工具、测试和二进制资源不自动带入目标架构，必须先证明对当前业务运行时有必要。

## 最近两日来源清单

| 状态 | 日期 | Commit | 主题 | 目标处理 |
|---|---|---|---|---|
| 已排除 | 2026-09-09 | `e143a4e` | Merge remote-tracking branch `origin/ShiinaKuroko` | 只作时间线标记，不移植合并提交 |
| 已排除 | 2026-09-09 | `2d51e04` | Merge 架构升级临时分支到 `ShiinaKuroko` | 只作时间线标记，不移植合并提交 |
| 已排除 | 2026-09-09 | `cdc987e` | `test(map): add navigation stress case` | 只评估测试价值，不带入旧 E2E 工具目录 |
| 已移植 | 2026-09-09 | `1d7fca7` | `fix(map): navigate sortie chapters through fixed OCR slots` | 已按新 `sortie_page/battle_page` 章节导航结构移植 |
| 已排除 | 2026-09-09 | `bc24d5e` | `feat(debug): bundle standalone debug toolkit` | 已确认不属于当前运行时，不移植二进制工具包 |
| 已移植 | 2026-09-08 | `9b000b4` | `fix(repair): unify task-level repair handling` | 已按当前任务/API/运行器边界手工移植 |
| 已移植 | 2026-09-08 | `02ce4ed` | `fix: default to full battle result collection` | 已按当前战斗计划/结算状态图手工移植 |
| 已排除 | 2026-09-08 | `cce7121` | `merge: add manual bath repair flow` | 只作合入标记，行为以其父级维修提交为准 |
| 已核对 | 2026-09-08 | `7443018` | `fix(repair): terminate task after manual bath dispatch` | 当前异常、Processor/调度器和任务路由已有等价实现 |
| 已核对 | 2026-09-08 | `450c88a` | `fix(repair): navigate to bath for manual repairs` | 当前普通/战役/决战澡堂显式路线已有等价实现 |
| 已核对 | 2026-09-08 | `e6d9fee` | `fix(navigation): add mode-specific bath routes` | 当前 `navigation.service` 已有来源明确路线 |
| 已核对 | 2026-09-07 | `c5a464c` | `fix(combat): accept flexible enemy rule conditions` | 当前解析器和 API 边界测试已有等价实现 |
| 已移植 | 2026-09-07 | `0577f15` | `fix(decisive): wait for map overlay to settle` | 已在决战进入地图后加入 2 秒稳定等待 |

## 逐项记录

### `e6d9fee` 模式专用澡堂导航

- 源文件：`autowsgr/ops/navigate.py`、`autowsgr/ui/navigation.py`、相关测试。
- 目标位置：`application/ui/navigation/service.py`、`navigation/graph/` 和各业务调用方。
- 当前结论：已核对。普通、战役和决战均使用目标导航服务中的来源明确路线；没有恢复无来源
  `BATTLE_PREP -> MAP` 边。
- 验证：澡堂导航/维修组合回归通过，目标 compileall 和 `git diff --check` 通过。

### `450c88a` 普通/决战手动维修进入澡堂

- 源文件：`autowsgr/ops/normal_fight.py`、`autowsgr/ops/decisive/handlers.py`、
  `autowsgr/ui/battle/repair.py`、测试。
- 目标位置：普通/战役/决战业务层、`navigation.service` 和准备页维修入口。
- 当前结论：已核对。普通、战役、决战调用方均已进入目标架构的维修入口并保留模式专用
  导航；决战继续使用暂离保存语义。
- 验证：普通/战役/决战澡堂链路和相关任务回归包含在 `269 passed` 中。

### `7443018` 手动澡堂维修后终止任务

- 源文件：`autowsgr/infra/exceptions.py`、`autowsgr/ops/repair.py`、
  `autowsgr/scheduler/scheduler.py`、`autowsgr/server/routes/task.py`、测试。
- 目标位置：`common.system` 异常、应用任务执行器/调度器、澡堂维修业务服务。
- 当前结论：已核对。`ManualRepairRequiredError`、Processor/legacy scheduler 终止传播、
  server 路由和澡堂目标派发已存在于目标；没有引入旧任务管理器结构。
- 验证：异常传播、任务终止、澡堂派发和相关 server/dispatch 回归包含在 `269 passed` 中。

### `9b000b4` 统一任务级维修处理（已移植）

- 源文件：`autowsgr/combat/plan.py`、`autowsgr/ops/normal_fight.py`、
  `autowsgr/ops/event_fight.py`、`autowsgr/ops/navigate.py`、server 任务契约。
- 目标位置：当前 `business.combat.plan`、`business.combat.bettle`、
  `application.ui.navigation`、`server.schemas`、`server.serializers` 和
  `server.task_manager`；战役/决战既有终止链保持不变。
- 当前结论：已移植 `repair_method=quick|bath`、全局配置兼容、澡堂派修等待、任务
  `REPAIRING` 状态和活动准备页专用回退路线；活动手动维修 TODO 已按最新源提交转为已实现。
- 冲突处理：未引入旧 `ops` 调度器；使用当前 `NormalFightRunner`、`Processor`、
  `TaskManager` 和现有 `application.ui.navigation` 边界，普通/活动路由显式传递维修状态回调。
- 验证：相关 API、任务、导航和运行器 focused 回归 `177 passed`；目标 compileall、
  import smoke、scoped pre-commit 和 `git diff --check` 通过。

### `02ce4ed` 默认完整战斗结果收集（已移植）

- 源文件：`autowsgr/combat/plan.py`、`autowsgr/combat/state.py`、
  `testing/combat/test_combat.py`。
- 目标位置：当前 `business.combat.plan`、`application.combat.engine.state` 和结算状态转移测试；保留当前数据模型命名。
- 当前结论：已将 `CombatPlan` 和状态图的默认值改为完整采集；显式 `False` 兼容路径保留，未引入旧架构模块或第二套状态源。
- 验证：`testing/combat/test_combat.py` 与 `testing/combat/test_result_dismiss_unit.py` 共 `145 passed`；目标 compileall、import smoke、scoped pre-commit 和 `git diff --check` 通过。

### `1d7fca7` 固定 OCR 槽位章节导航（已移植）

- 源文件：`autowsgr/ui/map/base.py`、`autowsgr/ui/map/data.py`、
  `autowsgr/ui/map/panels/sortie.py`、地图测试。
- 目标位置：`application/ui/controller/operations/sortie_page/battle_page/` 的
  `constants.py`、`data.py`、`recognition.py`、`base.py` 和 `sortie.py`。
- 当前结论：已将动态高亮条猜测替换为固定五槽位 OCR、标题回检和可证明槽位点击；
  OCR 二值化重试放在 `recognition.py`，旧高亮读取入口仅保留给诊断工具。
- 冲突处理：源提交把 OCR 槽位实现放在旧 `BaseMapPage`，目标按 UI Controller 规范
  下沉到现有 `battle_page/recognition.py`，页面只委托读取；删除旧 `click_chapter` 前
  已同步唯一工具消费者到 `click_chapter_slot`。
- 验证：地图 focused 回归 `28 passed`；`tools/check_sortie_api.py`、目标 compileall、
  import smoke、scoped pre-commit 和 `git diff --check` 通过。

### `0577f15` 决战浮层稳定等待（已移植）

- 源文件：`autowsgr/ops/decisive/handlers.py`、决战单元测试。
- 目标位置：`business/combat/decisive/handlers.py` 的地图进入状态处理器。
- 当前结论：已在点击进入地图后、设置 `WAITING_FOR_MAP` 前加入 2 秒动画稳定等待，
  复用既有等待截止时间和状态，不新增第二套 retry。
- 验证：决战 focused 回归 `4 passed`；目标 compileall、import smoke、scoped pre-commit
  和 `git diff --check` 通过。

### `c5a464c` 规则拼写兼容（已核对）

- 源文件：`autowsgr/combat/rules.py`、规则兼容测试和 API Schema 测试。
- 目标位置：`business/combat/rules.py` 的 `_parse_legacy_condition()` 及现有规则测试。
- 当前结论：目标已包含大小写、组合运算符空格兼容，且保持单等号非法；不重复移植。
- 冲突处理：目标路径和 API Schema 已使用新的解析器，不引入旧 `server` 或规则副本。
- 验证：规则解析、Schema 和 Processor 组合回归 `269 passed`，目标 compileall 和
  `git diff --check` 通过。

### `bc24d5e` 调试工具包

- 源文件：独立 `tools/debug_toolkit/`、二进制 ADB 文件、工具测试。
- 当前结论：默认不移植。它是开发辅助和二进制资源，不是架构升级运行时功能；只有
  目标环境明确需要且能单独纳入工具边界时才另行处理。
- 验证：本阶段只记录审查结论，不运行或复制二进制资源。

### `cdc987e` 地图导航压力测试

- 源文件：`function/e2e_runner/cases/map_navigation.py`。
- 当前结论：只评估测试场景能否映射到新 `MapPage` API，不把旧 E2E 框架整体迁移。
- 验证：若有可复用断言则在目标测试中重写，否则记录为不移植。

## 2026-09-09 初始核对

- 已按 `ShiinaKuroko` 分支当前指针 `e143a4e` 盘点最近两日提交；合并提交只作时间线标记，`bc24d5e` 调试工具包和 `cdc987e` 旧压力测试暂不移植。
- `02ce4ed` 的源实现不应整文件搬运：旧 `autowsgr/combat/plan.py` 对应目标 `business/combat/plan.py`，旧 `autowsgr/combat/state.py` 对应目标 `application/combat/engine/state.py`。
- 基线命令对空计划和默认 MAP 状态图的“完整采集”断言失败，证明该功能尚未在目标架构生效；失败输出和下一步已记录在 `progress.md`。

## 2026-09-09 已有功能核对

- `e6d9fee`、`450c88a`、`7443018` 和 `c5a464c` 的有效行为已在目标架构中存在，分别
  覆盖来源明确的澡堂路线、普通/战役/决战维修调用、手动维修终止传播和规则拼写兼容。
- `cce7121`、`e143a4e`、`2d51e04` 是合并/时间线标记；`bc24d5e` 是含二进制的调试工具包；
  `cdc987e` 是旧 E2E 压力测试，均不纳入运行时移植。
- 上述核对的组合 focused 回归为 `269 passed`；没有执行 cherry-pick、merge 或远程操作。

## 总结状态

- 台账建立完成，最近两日来源时间线已盘点；`02ce4ed`、`9b000b4`、`1d7fca7` 和
  `0577f15` 已完成手工移植，既有功能和排除项也已核对，阶段三进入复核。
- 合并提交不作为移植对象；调试工具包默认排除。
- 任何功能标记“已移植”前，必须写入目标文件、调用链、冲突解决和 focused 验证结果。
