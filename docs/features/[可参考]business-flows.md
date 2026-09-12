# 业务链路重塑清单

> 目标：一个功能一个功能梳理，代码的业务逻辑与实际业务逻辑相同，细节重新定义。
> 用法：逐条对照「实际业务 → 现状实现 → 差异 → 新定义」，重塑一条勾一条。

**图例**：✅ 已重塑 | 🔍 已梳理待拍板 | ⬜ 未开始

---

## 梳理顺序（按链路依赖 + 使用频率）

1. ⬜ 启动登录 —— 一切的起点
2. ⬜ 导航 —— 页面跳转公共底座
3. ⬜ 常规战 —— 最复杂最高频的核心业务
4. ⬜ 远征 —— 挂机循环骨架（收-修-派）
5. ⬜ 修理 —— 与远征咬合
6. ⬜ 战役 —— 耗尽型小战斗
7. ⬜ 演习 —— 耗尽型小战斗
8. ⬜ 建造 —— 独立小功能
9. ⬜ 烹饪 —— 独立小功能
10. ⬜ 解装 —— 独立小功能
11. ⬜ 奖励 —— 独立小功能
12. ⬜ 换编队 —— 编队页换船
13. ⬜ 活动战 —— 常规战的复杂变体
14. ⬜ 决战 —— 多舰队复杂变体
15. ⬜ 每日挂机 —— 全部理清后自然清楚

---

## 1. 启动登录 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/startup.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/startup.py)）：

```
launcher.launch()                     # 配置加载 → 连接设备 → 建 OCR → GameContext
  └─ ensure_ready()                   # 游戏未就绪时:
       ├─ start_game()                # 检查前台应用是否为游戏, 不是则启动 intent
       ├─ login()                     # 登录循环 (最多10次):
       │    ├─ screenshot() → 识别登录页
       │    ├─ 登录页 → click(进入游戏按钮)
       │    ├─ 网络错误弹窗 → 点确认重试
       │    ├─ 远程登录弹窗 → 点确认
       │    └─ 主页 → 成功
       └─ handle_login_result()
start_screen_page.py                  # 启动屏页面识别 (公告/新闻/签到处理)
main_page/controller.py               # 主页控制器: 关闭弹窗/公告/签到等
```

**待梳理问题**：
- [ ] 登录页公告/新闻弹窗处理的完整清单
- [ ] 换区功能（constants/coordinates/login.yaml 已有坐标，代码未接入）
- [ ] 什么状态算"启动成功"（主页？公告关闭后？）
- [ ] 断线重连（游戏中途掉线）算不算启动登录的职责

---

## 2. 导航 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/navigate.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/navigate.py) + [ui/navigation.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ui/navigation.py)）：

```
goto_page(ctx, 目标页)
  ├─ identify_current_page()          # 截图识别当前页 (5次重试+全量兜底)
  ├─ find_path(当前页, 目标页)         # NAV_GRAPH 21条边 BFS 寻路
  └─ 逐边执行 NavEdge.func()          # 每条边 = 一个页面跳转函数 (点击+等待)
                                     # 循环中维护 ui_stack (页面来路栈)
```

**NAV_GRAPH 现有页面**：main / map / mission / backyard / sidebar / bath / canteen / decisive / build / intensify / friend / event / 其余页

**待梳理问题**：
- [ ] 新坐标 YAML（common/main/login）与 NAV_GRAPH 边函数的对接
- [ ] 页面识别失败的根本处理策略（现状：5次重试+全量兜底，然后呢？）
- [ ] 导航中的弹窗干扰（公告/奖励弹窗挡路）如何统一处理
- [ ] ui_stack 的去留（任务级新上下文决策下）

---

## 3. 常规战 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/normal_fight.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/normal_fight.py) NormalFightRunner.run()）：

```
run() 一次完整常规战:
  ├─ _enter_fight()                   # 导航到地图 → 选章节/地图 → 选难度 → 进入准备页
  ├─ _prepare_for_battle()            # 选舰队 → (换船) → 补给 → 修理 → 读取舰队信息
  ├─ _do_combat()                     # CombatEngine.fight() 状态机:
  │    START_FIGHT → FIGHT_CONDITION → SPOT_ENEMY → FORMATION
  │    → FIGHT_PERIOD → RESULT → PROCEED(继续/撤退) → GET_SHIP(掉落)
  │    每个节点 = 识别页面 → 按计划规则决策 → 点击
  └─ _handle_result()                 # 结算: 战果/掉落/资源/船坞满处理
循环 N 次由调用方控制 (times 参数)
```

**待梳理问题**：
- [ ] 一次"出击"的业务边界（现状：进场到结算算一次）
- [ ] 中途船大破的应急逻辑（撤退？修理？）
- [ ] 船坞满时的解装触发
- [ ] 停止条件（次数/掉落船数/胖次数/快修上限）的完整定义
- [ ] 战斗中被打断的恢复语义（重复任务打断设计——用户留待讨论）

---

## 4. 远征 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/expedition.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/expedition.py)）：

```
collect_expedition()                 # 收取全部完成远征 (远征页 → 逐个收取)
collect_resources()                  # 收资源 (主页资源栏)
collect_rewards()                    # 收任务奖励 (任务页 → 全部领取)
have_ship()                          # 检查远征队列状态
run_expedition()                     # 派遣逻辑: 收 → (修) → 派新
调度: triggers.ExpeditionTrigger     # 定时轮询 (interval 配置, 默认10分钟)
```

**待梳理问题**：
- [ ] 收-修-派的完整循环业务规则（哪些船修哪些直接派）
- [ ] 远征队列与舰队占用的冲突处理（远征占用舰队时战斗不能用）
- [ ] 手动收远征与自动轮询的边界
- [ ] GUI 手动触发 vs 挂机定时触发是否同一套逻辑

---

## 5. 修理 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/repair.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/repair.py)）：

```
quick_repair()                       # 战斗准备页快修 (消耗快修道具)
bath_repair_all()                    # 浴场慢修 (有空槽就塞满)
调度: triggers.BathRepairTrigger     # 深夜时段自动浴场修理
bathroom 状态缓存                    # GameContext.bathroom 槽位记忆
```

**待梳理问题**：
- [ ] 快修 vs 慢修的选择策略（什么时候值得用快修）
- [ ] 浴场槽位状态的记忆方式（任务级新上下文决策下）
- [ ] 修理与战斗排队的互斥（等船修好再打 vs 换船打）
- [ ] 黑名单（bath_repair_blacklist）业务规则

---

## 6. 战役 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/campaign.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/campaign.py) CampaignRunner）：

```
run() → 进入战役面板 → 选战役 → 选难度 → 准备 → 战斗 → 结算
每日次数限制: battle_times_exceed 模板识别 → 自动停
调度: triggers.CampaignTrigger (每日耗尽型, 优先级5)
```

**待梳理问题**：
- [ ] 每日 10 种战役的业务规则（哪些值得打、次数）
- [ ] 战役与常规战的资源争夺
- [ ] 打完的判定（次数耗尽自动停的可靠性）

---

## 7. 演习 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/exercise.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/exercise.py) ExerciseRunner）：

```
run() → 演习面板 → 刷新对手列表 → 选对手 → 准备 → 战斗 → 结算 → 下一个
每日限制: 演习次数识别 → 耗尽停
调度: triggers.ExerciseTrigger (每日耗尽型, 优先级10, 分2/3时段)
```

**待梳理问题**：
- [ ] 对手选择策略（战力？顺序？）
- [ ] 2/3 时段刷新的业务规则
- [ ] 演习舰队与常规战舰队的复用

---

## 8. 建造 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/build.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/build.py)）：

```
build_ship()/build_equipment()       # 开建 (燃料/弹药/钢材配比)
fast_build()                         # 快建 (消耗快建道具)
collect()                            # 收取完成的建造
循环模式: 开建 → 等待 → 收取 (定时触发)
```

**待梳理问题**：
- [ ] 建造循环的业务节奏（多久收一次）
- [ ] 资源不足时的处理
- [ ] 快建的使用策略

---

## 9. 烹饪 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/cook.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/cook.py)）：

```
cook()                               # 做菜 (食堂 → 选食谱 → 开始)
收取: have_cook 模板识别 → 收菜
```

**待梳理问题**：
- [ ] 食谱选择策略
- [ ] 收菜节奏

---

## 10. 解装 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/destroy.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/destroy.py)）：

```
destroy_ships()                      # 船坞满时按舰种过滤拆船
触发: 船坞满 (战斗结算时检测 dock_full)
```

**待梳理问题**：
- [ ] 哪些船该拆（白名单舰种外的全拆？）
- [ ] 解装与掉落统计的联动（拆掉的船算不算"获得"）

---

## 11. 奖励 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/reward.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/reward.py)）：

```
collect_daily_bonus()                # 每日签到
collect_rewards()                    # 任务奖励全部领取
```

**待梳理问题**：
- [ ] 收奖励的触发时机（登录后？定时？）
- [ ] 与远征轮询的绑定关系（现状：随远征周期收）

---

## 12. 换编队 ⬜

**实际业务**：待用户描述

**现状实现**（[ui/battle/fleet_change/](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ui/battle/fleet_change/) 7文件子系统）：

```
准备页编队校验: OCR舰名/等级/舰种 → 主选/备选匹配 → 不满足则进船池选船
全流程含: 槽位对齐 / 多余删除 / 主选兜底 / 最终验证 OCR
```

**待梳理问题**：
- [ ] 主选/备选的完整业务规则（严格/宽松校验——memory 已有部分约束）
- [ ] 换船失败的重试语义（有限重试后明确退出——memory 已有约束）

---

## 13. 活动战 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/event_fight.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/event_fight.py)，与 normal_fight 共用 NormalFightRunner）：

```
chapter 为 E/H → 活动入口 → α/β入口选择 → 难度 → 战斗 (状态机同常规战)
计划文件: data/map/event/<日期>/*.yaml
```

**待梳理问题**：
- [ ] 活动图数据的热更新方式（新活动开时如何加图）
- [ ] α/β 入口的业务含义

---

## 14. 决战 ⬜

**实际业务**：待用户描述

**现状实现**（[ops/decisive/](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/ops/decisive/) 7文件）：

```
DecisiveController: 章节推进 → 地图导航(磁盘购买) → 多舰队编队 → 战斗 → 结算
状态: state.py 决战内进度记忆
```

**待梳理问题**：
- [ ] 决战进度的持久化（跨任务记忆——与任务级新上下文的张力）
- [ ] 磁盘购买的业务规则
- [ ] 多舰队协同的完整逻辑

---

## 15. 每日挂机 ⬜

**实际业务**：待用户描述

**现状实现**（[scheduler/daily_plan.py](file:///c:/ShiinaKuroko/01.Project/AutoWSGR/autowsgr/scheduler/daily_plan.py) + triggers.py + TaskScheduler）：

```
build_daily_plan(): usersettings.yaml daily_automation 段 → 触发器注册
TaskScheduler.run_daily():
  优先级队列: 远征(0) > 收奖(1) > 战役(5) > 演习(10) > 常规战(100) > 浴场修理(200)
  跨日重置: 0点刷新每日耗尽型任务
  空闲填充: 常规战无限打, 抢占浴场修理
```

**待梳理问题**：
- [ ] 优先级体系的完整定义（现状数字是否合理）
- [ ] 跨日重置的精确时刻和内容
- [ ] 挂机与 GUI 手动任务的冲突仲裁（谁打断谁）

---

## 附：全局待决策问题（梳理过程中积累）

| 问题 | 状态 |
|------|------|
| 任务级新上下文（用户已拍板方向） | ✅ 原则已定，细节随各功能梳理落地 |
| 主页锚点不变量 | ✅ 原则已定 |
| 坐标 YAML 格式不可变 | ✅ 原则已定 |
| 统一调度器形态（简化版：调度统一优先，原子化后置） | 🔍 方向已定，随业务梳理细化 |
| 重复任务（出征N次）的打断设计 | ⬜ 用户留待讨论 |
| GameContext 状态字段的最终归宿 | ⬜ 随各功能梳理逐个处理 |
