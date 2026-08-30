# 演习实机验证日志报告

日期：2026-08-30  
仓库：`C:\ShiinaKuroko\01.Project\.worktrees\20260830-exercise-team-contract-4c71\AutoWSGR`  
设备：`127.0.0.1:16384`，`1280x720`  
模式：FastOCR / CPU  
最终日志目录：`logs/e2e_tools/exercise/20260830_211026/`

## 执行命令

```text
uv run python tools/e2e/run.py --with-ocr --fast-ocr exercise \
  --yaml testing/fixtures/exercise_team2.yaml \
  --rivals-limit 1 --relay --with-init \
  --checks expedition_check,reward_check,expedition_check,reward_check,expedition_check
```

## 结果

E2E 总体结果：`FAIL`。失败发生在第一次选船，未进入战斗；不是初始化、导航、任务插入或日志通道失败。

框架最终完成了：

- 初始化到首页：通过。
- 无浮层：通过。
- YAML 加载：通过，六槽队伍定义成功解析。
- 演习入口：通过。
- 第一次远征插入：通过，收取 4 支远征并回首页。
- 编队页面入口：通过。
- 第一次任务插入：通过，领取任务奖励并回首页。
- 选船完成断点：已触发。
- 第二次远征插入：通过。
- 最终清理回首页：通过。
- 设备断开：通过。

未执行到：

- `before_start` 出征前断点。
- `rival_done` 战斗结束断点。
- 战斗引擎、战果识别和战斗结束日志。

## 断点执行流

```text
panel_ready
  -> paused exercise
  -> done expedition_check
formation_entered
  -> paused exercise
  -> done reward_check
ship_selected
  -> paused exercise
  -> done expedition_check
编队重试
  -> 目标舰船不可用
  -> failed exercise
```

E2E 断言中“接力五断点全部完成”“最终演习完成”“后勤检查完整序列”失败，原因是编队前置条件失败；“终态主页面”和清理断言通过。

## 日志核对

日志文件：

- `logs/e2e_tools/exercise/20260830_211026/autowsgr_2026-08-30.log`
- `logs/e2e_tools/exercise/20260830_211026/autowsgr_2026-08-30.debug.log`

| 任务书日志 | 观察结果 | 判断 |
| --- | --- | --- |
| `演习编队加载` | `executor.py:86` 多次出现 | 正常 |
| `选择对手：1号` | `operations.py:55` 出现 | 正常 |
| `选择队伍：2` | `operations.py:72` 出现 | 正常 |
| `进入舰队编成` | `operations.py:73` 出现 | 正常 |
| `当前队伍不满足演习编队` | 准备页检测到六槽为空后出现 | 正常 |
| `开始选择 N 号位舰船` | 六个槽位均输出目标和候选 | 正常 |
| `当前舰船为严格校验规则` | 每次严格校验尝试均输出 | 正常 |
| `目标舰船：名称 / 类型 / >=100，识别失败，当前次数 N` | 目标名、舰种和等级均输出，次数为 1/2/4 | 正常 |
| `目标舰船...当前次数耗尽，流程终止！` | 六个目标槽位均输出 | 正常 |
| `进入战斗` | 未出现 | 前置编队失败，符合预期 |
| `战斗结束，演习结果` | 未出现 | 未进入战斗，符合预期 |

本次所有已到达阶段的业务日志都存在，名称、舰种、等级和重试次数没有丢失。没有出现宽泛校验日志，是因为 fixture 中六个槽位全部是严格规则；没有出现战斗日志，是因为账号无法识别目标舰船。

## 失败根因

日志中的确定性根因是：

```text
[准备页] 当前编队: [None, None, None, None, None, None]
[准备页] OCR校验: 不通过，进入换船流程
[准备页] 换船失败: 目标槽位 0 的主选和备选均不可用
[OCR] 目标舰船：85工程 / 航母 / >=100，识别失败，当前次数耗尽，流程终止！
```

本次账号没有可被当前选船页 OCR/DLL 识别的 `85工程`、`AIII`、`炽热·改`、`考文垂`、`絮弗伦`、`基阿特·改`。处理器随后按硬重试策略重复初始化并最终 `failed`，没有把失败伪装成完成，也没有进入战斗。

## 前置导入修复记录

本批第一次启动在进入地图前发现 `MainPage` 的出征检查器仍导入旧 `autowsgr.ui.map`，触发旧 `autowsgr.ui.page` 缺失。修复为直接导入 `autowsgr.infra.ui.pages.map` 后，第二次启动成功走到演习编队页；对应代码为 `autowsgr/infra/ui/pages/main_page/controller.py` 的 `Target.SORTIE` 分支。

第一次日志目录：`logs/e2e_tools/exercise/20260830_210633/`。

## 结论

日志展示和日志语义符合当前已执行链路；本次不是日志缺失导致的失败，而是账号舰船数据不满足六槽 YAML。要验证 `before_start`、`rival_done` 以及战斗结果日志，需要账号具备该队伍的六艘可识别舰船，或下一轮使用已确认可用的队伍配置。
