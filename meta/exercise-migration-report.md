# Sakuya 演习迁移报告

日期：2026-08-30<br>
工作分支：`codex/20260830-sakuya-exercise-consolidated-7a6c`<br>
范围：AutoWSGR 后端演习垂直切片；未修改 AutoWSGR-GUI 源码。

## 结论

演习链路已在 Sakuya 替代架构中形成可运行的完整主路径：

```text
YAML path -> Request admission -> Processor -> ExerciseExecutor
          -> infra map/preparation/ship OCR -> CombatEngine(EXERCISE)
          -> result/events -> home cleanup
```

静态门禁全部通过。五次实机预算已用完，其中三次主路径/交接通过；一次按
用户给定 YAML 正确失败（账号缺船），一次按跨队伍占用限制正确 fail-closed。

## 代码落点

- `business/combat/exercise/`
  - `spec.py`：YAML 字段准入、演习默认模式/夜战、主选与备选规则转换。
  - `executor.py`：对手选择、编队、补给/修理、战斗、计数、暂停/停止断点、
    事件和首页收尾；新任务统一由 Processor 构造执行器。
- `infra/base/combat/`
  - 出征准备页、舰队调整、选船页、地图面板和船池 OCR 从旧 UI 目录迁移；
    旧路径保留轻量 alias，未复制第二套实现。
- `dispatch` / `server`
  - YAML 请求冻结、任务类型准入、有限 `count`、优先级插队、暂停重排和
    HTTP 结果投影。
- 其他修复
  - 活动页出击模板限定右下 ROI，避免误识别准备页标题。
  - 准备页异常收尾先回地图再回首页；暂停回退成功后清除本地准备状态。
  - OCR 终止日志只报告未满足/未验证槽位，并包含名称、舰种、等级约束。

## 静态验证

| 门禁 | 结果 |
| --- | --- |
| 全量 pytest | `1073 passed` |
| 演习/准备页/活动页 focused tests | `145` 及 `14` 通过；交接 focus `62` 通过 |
| `compileall` | 通过 |
| 迁移模块直接 import | 通过（map、battle preparation、exercise、reward） |
| Ruff check/format | 新增及直接修改的业务/dispatch/server/event/test 文件通过 |
| `git diff --check` | 通过 |

被迁移的旧 UI 文件仍有既有复杂度和风格告警；本批未借迁移名义扩大清理范围。

## 实机记录

| 次数 | 输入/断点 | 结果 | 关键证据 |
| --- | --- | --- | --- |
| 1/5 | 用户六槽 YAML，队伍 2，无断点 | 按规则失败 | 账号没有 `S-198/S189`、`阿尔汉格尔斯克`、`水貂`；同时暴露活动页误匹配，随后静态修复 |
| 2/5 | 账号有效四船 YAML，队伍 2 | 通过 | 已有编队被识别为满足，无重复换船；对手 1 战斗成功；日志 `logs/e2e_tools/exercise/20260830_071041/` |
| 3/5 | 账号有效四船 YAML，队伍 1 | 正确失败 | 舰船已归属队伍 2，游戏拒绝跨队伍分配；最终 OCR 拒绝无效队伍，清理成功；日志 `logs/e2e_tools/exercise/20260830_071528/` |
| 4/5 | 队伍 2，`panel_ready` + `expedition_check` | 通过 | 实际收取 4 支远征后恢复并完成对手 2；日志 `logs/e2e_tools/exercise/20260830_072351/` |
| 5/5 | 队伍 2，`before_start` + `reward_check` | 通过 | 实际领取任务奖励后恢复并完成对手 3；日志 `logs/e2e_tools/exercise/20260830_073147/` |

每次完整 E2E 都由框架初始化到首页，结束时验证首页、执行清理并断开设备。
游戏进程异常恢复逻辑使用初始化入口，没有重放已经执行的点击。

## 契约与影响边界

- 没有 GUI 页面、样式、交互逻辑或 GUI 文件变更。
- 没有修改最终 GUI/后端协议；新增能力沿用 YAML 路径和现有任务结果投影。
- 旧编队、选船、修理导入路径保留 alias，普通/决战既有消费者的调用方式未改。
- `task_type`、优先级、`count` 和 `extre` 均由后端 Processor 统一解释；GUI
  适配仍可在后续联调切片完成。

## 未完成项与后续建议

1. 用户给定六槽 YAML 需要具备对应舰船的账号才能验证完整战斗；当前账号数据
   不满足，不能把四船 smoke 结果冒充六船验收。
2. 跨队伍可用性目前依靠点击后的最终 OCR 才发现，导致失败重试耗时较长；后续
   可增加进入选船页前的“已归属其他队伍”预检，并保持 fail-closed。
3. `ship_selected` 和 `rival_done` 独立断点已有静态覆盖，但本批五次预算优先用于
   主路径、远征和奖励交接，未再追加实机操作。
4. HTTP 仍使用现有单 worker `TaskManager`；更大范围的 Processor/Runtime 所有权
   收口属于后续架构切片。
5. 被迁移 UI 模块的既有 Ruff 复杂度告警应在单独的 infra 瘦身批次处理。

## 提交检查点

- AutoWSGR：`3ccd887` (`feat(exercise): migrate exercise chain to Sakuya`)
- 目录边界收口：`e26f91f`（移除兼容层）、`b18337d`（集中战斗基建目录）
- 协调记录：`3e382ac`、`08bf713`、`bcb121b`、`dd0d7c7`、`f12c089`
- 本报告及最终纪要更新将在当前协调分支追加提交。
