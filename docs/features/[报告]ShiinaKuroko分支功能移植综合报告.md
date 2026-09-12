# ShiinaKuroko 分支功能移植综合报告

主任务：`20260830-autowsgr-upgrade`

阶段：阶段三，高优先级功能手工移植

日期：2026-09-09

目标工作区：`C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/20260830-autowsgr-upgrade`

源分支基线：`ShiinaKuroko@e143a4e`

## 一、执行结论

已按台账核对 `ShiinaKuroko` 最近两日的 13 条提交记录，没有对目标工作区执行
`cherry-pick`、`merge`、覆盖或远程操作。4 条有效功能提交已按当前架构手工移植，
4 条此前已有等价实现的功能已核对，2 条合并提交、1 个调试工具包和 1 条旧 E2E
压力测试已明确排除。

阶段三聚合 focused 回归为 `408 passed`；全量 `compileall`、修正后的 import smoke、
目标文件 pre-commit 和 `git diff --check` 通过。

## 二、逐项结果

| Commit | 结论 | 目标位置 | 处理摘要 |
|---|---|---|---|
| `02ce4ed` | 已移植 | `business.combat.plan`、`application.combat.engine.state` | 默认完整采集战果；显式 `False` 仍走快速路径 |
| `9b000b4` | 已移植 | `business.combat.bettle`、`application.ui.navigation`、`server` | 维修方式契约、澡堂等待、`REPAIRING` 状态和活动路线 |
| `1d7fca7` | 已移植 | `operations/sortie_page/battle_page` | 固定五槽位 OCR 章节导航，替换高亮条猜测 |
| `0577f15` | 已移植 | `business.combat.decisive.handlers` | 进地图点击后等待 2 秒再进入地图等待态 |
| `e6d9fee` | 已核对 | `application.ui.navigation.service` | 普通/决战来源明确澡堂路线已存在 |
| `450c88a` | 已核对 | 出征准备、普通/战役/决战业务层 | 手动维修澡堂导航已存在 |
| `7443018` | 已核对 | `common.system`、`dispatch`、任务路由 | 手动维修终止异常传播已存在 |
| `c5a464c` | 已核对 | `business.combat.rules` | 规则大小写与组合运算符空格兼容已存在 |

## 三、架构适配

### 默认完整战果采集

旧 `autowsgr/combat/plan.py` 和 `autowsgr/combat/state.py` 没有直接搬运。目标分别
对应 `business/combat/plan.py` 和 `application/combat/engine/state.py`，默认值统一为
完整采集，结算处理器继续消费唯一的 `plan.collect_result_info` 状态。

### 任务级维修

`repair_method` 由 `server.schemas.CombatPlanRequest` 进入 serializer，再写入
`business.combat.plan.CombatPlan`。普通/活动运行器按 `quick`、`bath` 和未声明三种
情况分派：任务级配置优先，未声明时兼容旧全局 `repair_manually`。`bath` 复用现有
澡堂派发服务并等待目标舰船恢复；`server.task_manager` 的 `REPAIRING` 是唯一任务
状态所有者，并保留设备占用、停止和进度语义。

活动出征现在使用独立的
`BATTLE_PREP -> EVENT_MAP -> HOME -> BACKYARD -> BATH` 路线；没有恢复无来源的
通用 `BATTLE_PREP -> MAP` 边。此前活动 TODO 已根据最新源提交转为实现。

### 固定槽位章节导航

页面专属点击坐标、OCR ROI 和白名单位于
`application/ui/controller/operations/sortie_page/battle_page/constants.py`；
`ChapterSlot` 和可证明槽位选择位于 `data.py`；章节文本解析、固定槽位 OCR 和二值化
复识别位于 `recognition.py`；`BaseMapPage` 只委托读取，`SortiePanelMixin` 负责点击
与导航流程。旧 `read_selected_chapter_y` 仅保留给 E2E 诊断，不再参与章节寻路。

### 决战进图等待

在既有 `WAITING_FOR_MAP` 状态转换中加入 2 秒稳定窗口，没有增加新状态、重复重试
或改变决战状态机的其他分支。

## 四、排除项

- `e143a4e`、`2d51e04`：合并/时间线标记，不作为功能提交移植。
- `cce7121`：合并标记，行为由其父级维修提交负责。
- `bc24d5e`：独立调试工具包，包含 ADB 二进制，不属于当前运行时。
- `cdc987e`：旧 E2E 压力测试框架；固定槽位主场景已在目标测试中按新 API 重写，
  不搬运旧工具目录。

## 五、验证证据

- `02ce4ed`：战斗计划/结算 focused `145 passed`。
- `9b000b4`：API、任务管理、维修、导航和运行器 focused `177 passed`。
- `1d7fca7`：地图 focused `28 passed`，`tools/check_sortie_api.py` 通过。
- `0577f15`：决战 focused `4 passed`。
- 既有维修、规则和 Processor 组合核对：`269 passed`。
- 阶段三聚合 focused：`408 passed`。
- `uv run --locked --dev python -m compileall -q autowsgr testing`：通过。
- 目标文件 `uv run --locked --dev pre-commit run --files ...`：通过；首次 Ruff 自动
  修正和测试替身契约错误已记录在 `task_plan.md` Errors。
- `git diff --check`：通过。
- 未运行真实模拟器/实机 E2E，也未修改 GUI；这些不作为本阶段“已实机验证”声明。

## 六、剩余风险

- `BathPage` 隐式 OCR 创建、选船 OCR 生命周期/私有 API、上下文优先级和 ROI/OCR
  混合职责仍按既有 `[todo]` 台账保留；本阶段没有改变用户重点维护的选船算法。
- `repairing` 是后端新增状态，当前只验证了 AutoWSGR server/WebSocket 侧；GUI 对该
  状态的展示和消费需在跨仓契约任务中单独验证。
- 澡堂派发服务原有的页面失败记录和上下文状态同步边界未在本阶段重写；实际游戏
  派修时仍需模拟器或实机验证。
- 当前工作区包含此前架构升级的广泛未提交改动，本报告不代表这些改动已经形成独立
  可发布提交，也不执行自动提交或合并。

## 七、交付物

- `meta/[台账]ShiinaKuroko分支功能移植台账.md`
- `meta/[报告]ShiinaKuroko分支功能移植综合报告.md`
- `task_plan.md`、`findings.md`、`progress.md`

下一阶段只读检查决战升级 debug worktree，产出参考移植计划，不在本阶段自动移植
或改变当前决战业务。
