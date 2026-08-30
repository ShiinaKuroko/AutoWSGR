# 演习实机验证日志报告

日期：2026-08-30<br>
仓库：`C:\ShiinaKuroko\01.Project\.worktrees\20260830-exercise-team-contract-4c71\AutoWSGR`<br>
设备：`127.0.0.1:16384`，`1280x720`<br>
模式：FastOCR / CPU<br>
最终日志目录：`logs/e2e_tools/exercise/20260830_220134/`

## 执行命令

```text
uv run python tools/e2e/run.py --with-ocr --fast-ocr exercise \
  --yaml testing/fixtures/exercise_team2.yaml \
  --relay --with-init \
  --checks expedition_check,reward_check,expedition_check,reward_check,expedition_check \
  --ship-name-alias '契卡洛夫=85工程' \
  --ship-name-alias '希尔德布兰德=AIII' \
  --ship-name-alias 'U-47·狼群=U-47' \
  --ship-name-alias 'U-47·帕斯卡=U-47' \
  --ship-name-alias '考佩斯=考彭斯'
```

## 结果

E2E 总体结果：`PASS`。映射参数生效，六槽编队完成，实际挑战页面提供的 5 个对手并全部完成战斗；不是初始化、导航、任务插入或日志通道失败。

框架最终完成了：

- 初始化到首页：通过。
- 无浮层：通过。
- YAML 加载：通过，六槽队伍定义成功解析。
- 演习入口：通过。
- 第一次远征插入：通过，回首页。
- 编队页面入口：通过。
- 第一次任务插入：通过，领取任务奖励并回首页。
- 选船完成断点：通过。
- 出征前奖励插入：通过。
- 战斗结束后远征插入：通过。
- 5 个对手均完成：通过。
- 最终清理回首页：通过。
- 设备断开：通过。

未执行到：

- 第六个对手：未出现；当前页面实现和实机状态均为 5 个对手。

## 断点执行流

```text
panel_ready
  -> paused exercise -> done expedition_check
formation_entered
  -> paused exercise -> done reward_check
ship_selected
  -> paused exercise -> done expedition_check
before_start
  -> paused exercise -> done reward_check
rival_done
  -> paused exercise -> done expedition_check
resume exercise
  -> rival 2 -> rival 3 -> rival 4 -> rival 5
  -> completed exercise
```

E2E 断言“接力五断点全部完成”“最终演习完成”“后勤检查完整序列”“终态主页面”及清理断言全部通过。

## 日志核对

日志文件：

- `logs/e2e_tools/exercise/20260830_220134/autowsgr_2026-08-30.log`
- `logs/e2e_tools/exercise/20260830_220134/autowsgr_2026-08-30.debug.log`

| 任务书日志 | 观察结果 | 判断 |
| --- | --- | --- |
| `演习编队加载` | `executor.py:86` 多次出现 | 正常 |
| `选择对手：1号` | `operations.py:55` 出现 | 正常 |
| `选择队伍：2` | `operations.py:72` 出现 | 正常 |
| `进入舰队编成` | `operations.py:73` 出现 | 正常 |
| `当前队伍不满足演习编队` | 准备页检测到六槽为空后出现 | 正常 |
| `开始选择 N 号位舰船` | 六个槽位均输出目标和候选 | 正常 |
| `当前舰船为严格校验规则` | 每次严格校验尝试均输出 | 正常 |
| `目标舰船：名称 / 类型 / >=100，识别成功！` | 六槽逐项输出名称、舰种和等级 | 正常 |
| `舰队编成完毕成员为` | 输出 6 个成员 | 正常 |
| `进入战斗` | 5 场均出现 | 正常 |
| `战斗结束，演习结果` | 5 场均出现 `success` | 正常 |

本次所有到达阶段的业务日志都存在，名称、舰种、等级和重试次数没有丢失。没有出现宽泛校验日志，是因为 fixture 中六个槽位全部是严格规则；严格规则、编队、出征和战果日志均正常。

## 前一轮失败根因

日志中的确定性根因是：

```text
[准备页] 当前编队: [None, None, None, None, None, None]
[准备页] OCR校验: 不通过，进入换船流程
[准备页] 换船失败: 目标槽位 0 的主选和备选均不可用
[OCR] 目标舰船：85工程 / 航母 / >=100，识别失败，当前次数耗尽，流程终止！
```

前一轮失败的直接原因是搜索框仍输入标准名 `85工程`，而账号实际使用自定义名 `契卡洛夫`，导致 DLL 定位到 0 行。当前修复同时把别名加入 OCR 舰名组，并在搜索框将标准名转换为自定义名；本轮日志已验证该路径。

## 前置导入修复记录

本批第一次启动在进入地图前发现 `MainPage` 的出征检查器仍导入旧 `autowsgr.ui.map`，触发旧 `autowsgr.ui.page` 缺失。修复为直接导入 `autowsgr.infra.ui.pages.map` 后，第二次启动成功走到演习编队页；对应代码为 `autowsgr/infra/ui/pages/main_page/controller.py` 的 `Target.SORTIE` 分支。

第一次日志目录：`logs/e2e_tools/exercise/20260830_210633/`。

## 结论

日志展示和日志语义符合当前已执行链路；自定义舰名映射已通过真实选船和 OCR 验证。实机页面实际只有 5 个对手，本轮完成 5 场并覆盖全部五个断点；若业务确实要求第六个对手，需要先补充页面数据/坐标契约，不能由执行器虚构。

## 2026-08-31 六轮任务验证

本轮日志目录：`logs/e2e_tools/exercise/20260831_072125/`。首次启动只在请求准入阶段
发现配置别名被误判为标准舰名，未进入演习；修复准入校验后仅重新启动一次同一参数流程，
首次失败没有消耗演习次数。

执行参数：六个单场请求，队伍按 `2→3→2→3→2→3` 切换，前两轮连续，第二轮完成后
插入后勤任务验证非连续导航；五个断点依次插入：
`expedition_check`、`reward_check`、`expedition_check`、`reward_check`、
`expedition_check`。

验证结果：

- 六个演习任务请求均完成，五个断点均触发并在主页面恢复。
- 队伍切换、连续任务、非连续任务和最终回首页均通过。
- 实际挑战对手为 1 至 5 号，五场战斗均记录 `战斗结束，演习结果: success`。
- 第六个任务请求读到 `ExerciseRivalStatus([N, N, N, N, N])`，按无对手正常空完成，
  没有虚构第六场战斗。因此 E2E 的“每轮恰好一场”断言失败，进程结果为 `FAIL`。
- 第 4 轮出现两次、第 5 轮出现一次战斗状态识别超时；框架自动 SL 重启后重试并最终
  完成，未另开 E2E 进程。

结论：本轮完成了六轮调度与全部指定交接场景，但没有完成用户要求的六场实际战斗。
当前演习页面实现只暴露五个对手，后续需要先确认游戏实际次数与对手列表的契约，再决定
是否扩展页面识别/滚动逻辑；本轮不再追加设备操作。
