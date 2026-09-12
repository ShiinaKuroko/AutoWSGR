# Fleet 业务流程重构综合报告

Task ID：`20260830-autowsgr-upgrade`

工作区：`AutoWSGR/.worktrees/20260830-autowsgr-upgrade`

分支：`codex/20260830-autowsgr-upgrade`

## 一、交付范围

本任务将 `application/ui/controller/fleet/` 重写为三个一级业务边界：

```text
fleet/
├── main_page/       # 出征准备页 UI 原子动作和主流程
├── formation/       # 编队识别、编队调整、编队选船
└── support/         # 补给、战役支援、维修
```

`fleet/__init__.py` 只提供稳定的准备页控制器、事实模型、维修策略和导航注册所需的
船池页面检查入口。上层业务通过 `BattlePreparationPage` 进入准备页流程，不再依赖
Mixin、旧 Controller 或 Fleet 内部深层实现。

## 二、主要结果

### 页面控制器

- `main_page/page.py` 只保留准备页主流程、页面检查、舰队/面板读取、点击、出征确认和
  页面返回。
- `prepare_and_start_battle()` 按“准备页检查 → 编队调整 → 补给 → 战役支援 → 维修 →
  最终快照 → 出征确认”编排，不实现 OCR、规则规划或维修算法。
- 船池页面返回动作接收调用方的页面 checker，消除了选船节点反向依赖准备页页面类的
  循环。

### 选船核心

- `formation/fleet_recognition/` 只生成 `FleetSnapshot`、舰名、占用、舰种和等级事实。
- `formation/fleet_adjustment/` 负责规则解释、主选/备选规划、成员调整、战役固定槽位
  和决战无搜索框分支。
- `formation/ship_selection/` 负责船池页面动作、船卡 OCR、约束判断和单舰选择流程。
- 三个节点通过显式组合和公开包入口连接，不使用 Mixin、动态代理或旧兼容出口。
- 初始 `FleetSnapshot` 由 `FleetAdjustment` 唯一持有，对齐节点通过显式参数接收；不再
  保存重复的对齐快照状态。

### 辅助功能

- `support/supply/` 负责自动补给状态和快速补给。
- `support/campaign_support/` 负责战役支援启用、关闭、耗尽判断和切换复查。
- `support/repair/` 负责损伤识别、维修策略、快速维修复查和手动维修中断。
- 手动维修只抛出带槽位信息的 `ManualRepairRequiredError`，不从 Fleet 内部调用澡堂
  导航。

## 三、旧实现清理

- 删除旧的 `preparation`、`fleet_status`、`fleet_change`、`shipyard_page`、Mixin、
  动态属性代理、`FleetChangeController`、`create_controller` 和旁路状态。
- 删除只验证旧准备页实现的旧测试，不恢复旧 patch 路径。
- 删除无消费者的 `use_new_fleet_change_algorithm` 决战配置字段、API 请求字段、路由
  透传和专门测试。
- `FleetSnapshot` 是页面识别事实；普通和战役业务在业务层通过 `ctx.get_ship()` 获取
  运行时 `Ship`，Fleet 不再提供旧 `FleetInfo.to_ships()`。
- 迁移的 `common/fleet.py` 已作为无设备依赖的规则值对象模块补齐统一文件说明。

## 四、规范治理

- Fleet 及 `common/fleet.py` 的 Python 文件均有统一的“模块功能 / 上层调用 / 下层依赖”
  文件说明。
- Fleet 内不使用 `as` 导入别名，不使用私有 `from ... import _name`。
- 坐标、ROI、颜色和页面校准留在对应 `constants.py`；识别文件只保留 OCR 算法参数，
  页面文件不定义校准值。
- `common` 没有反向导入 Fleet，生产代码没有从 Fleet 子包深层导入；运行时顶层依赖图
  无循环。

## 五、验证结果

- Focused pytest：`230 passed`。
- Fleet、配置/API、普通/战役/演习和澡堂导航相关回归均包含在上述结果中。
- `python -m compileall -q`：通过，覆盖 Fleet、`common/fleet.py`、配置和 server schema。
- Fleet 根入口、formation 入口和导航注册 import smoke：通过。
- `tools/check_sortie_api.py`：通过。
- Fleet 结构、文件说明、导入别名、私有导入、校准归属、common 反向依赖、生产深层
  导入、旧符号和运行时依赖图静态门禁：通过。
- 目标文件 scoped pre-commit：通过，Ruff、Python AST、格式和 codespell 均通过。
- `git diff --check`：通过（仅有既有 `meta/.gitignore` 的换行提示）。

## 六、已知边界

- 本任务没有执行真实游戏或模拟器 E2E；页面模板、像素校准、OCR 稳定性和跨模式实机
  返回路径仍需现场验证。
- `formation/fleet_recognition/recognition.py` 仍沿用既有 `common.vision.ocr` 私有匹配
  能力，留给 OCR 专题处理；本任务未扩散新的私有 API。
- 船池和编队识别的部分校准仍来自 `common.calibration.choose_ship`，因为通用
  `common.vision.ship_list` 仍消费同一校准源；后续 OCR/ROI 专题再决定是否下沉或拆分。
- 活动、远征准备页的真实页面差异尚未确认，相关适配保留在后续业务联调范围。
- 仓内历史报告可能保留旧架构路径，这是历史事实记录，不是当前可导入入口。

## 七、交付状态

本任务已创建 commit `3b69518`（`refactor(ui): complete controller architecture migration`）。
未执行 merge、cherry-pick、push、reset、stash 或 worktree 清理；`.pytest_tmp/` 仅为测试
临时产物，未纳入提交。任务书和 `task_plan.md` 均已标记 `done`。
