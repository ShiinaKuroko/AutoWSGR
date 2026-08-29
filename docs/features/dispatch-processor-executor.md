# 处理器-执行器调度架构 — 演习链路迁移进度

> 交接文档 (2026-08-24)。本文档面向接手后续开发的 agent, 包含架构背景、
> 硬约束约定、当前进度与待办。阅读本文档后应能直接继续开发, 无需考古对话。

## 一、项目背景

### 1.1 任务目标

将 AutoWSGR 后端从"scheduler 直接驱动业务函数"的旧架构, 迁移到
**处理器-执行器** 两级调度架构, 并以演习 (exercise) 链路作为第一块试金石。

架构动机 (用户敲定的核心模型):

```
请求 (GUI HTTP / CLI / 定时器 / 下游依赖)
    │
    ▼
处理器 (dispatch.processor)  ← 所有请求的必经大脑
    │  ① 分辨请求 (来源 + 领域)
    │  ② 理解意图 (task_type + params, 读 YAML 或 GUI payload)
    │  ③ 查任务上下文 (当前正在跑什么, 是否可打断)
    │  ④ 决策 (直接执行 / 打断让路 / 排队)
    ▼
执行器 (business.*.*Executor)  ← 被动域专家
    │  接到处理器指令才开始工作:
    │  导航器导航到目的地 → 执行域内业务操作 → 回主页上报结果
    ▼
游戏 (点击 / 截图 / OCR 仅是任务内部步骤)
```

### 1.2 业务需求 (演习链路的具体验收标准)

用户对演习链路的行为定义 (原话归纳):

1. 用户提交演习 → 程序进入演习流程, **持续挑战直到没有可挑战对手** → 任务结束。
2. 中途若插入更高优先级任务 (如远征检查): 在**断点**处暂停,
   回主页让路 → 处理高优任务 → 处理完成后**继续演习**
   (已挑战过的对手在游戏中置灰, 重新识别自动跳过) → 直到没有对手。
3. **计数粒度 = 一个对手**: 每打完一个对手计数 +1
   (旧逻辑是打完全部对手才算一次, 本次变更的核心点)。
4. 两个执行模式: 完整模式 (打光全部, 默认) 与限额模式 (`rivals_limit=N`,
   N=1 为只打一次, 兼容老定时触发器)。

## 二、架构约定 (硬约束, 不可违反)

以下约定来自用户明确敲定 + 项目记忆, 实现必须服从:

### 2.1 调度模型

- **所有请求必须经过处理器**, 处理器具备优先级分辨功能;
  禁止任何入口绕过处理器直接驱动执行器。
- **打断决策归属处理器**, 禁止执行器或链路自查中断:
  处理器查上下文判断可打断性 (选船中=可打断, 出征中=原子不可打断),
  可打断则通知执行器跑到安全点停 → 回主页 → 处理加急请求;
  不可打断则高优先级请求排队等任务完成。
- **任务内部依赖** (如战斗中船损修理) 由 YAML 在任务开始前声明,
  执行器直接调用对应功能后继续任务, 不经过处理器;
  处理器只处理**外部新请求**与正在运行任务之间的打断决策。
- **执行器为被动域专家**: 接到处理器指令才开始工作;
  工作模式 = 找导航器导航到目的地 → 执行域内业务操作 → 回主页上报结果。

### 2.2 断点与锚点

- **断点免费藏在等待里**: 执行器基类 `_wait()` 在等待前检查暂停信号,
  收到信号 → 回主页 (`goto_page(MAIN)`) → 上报 `paused` → 抛 `TaskPaused`
  让出执行权。子类用 `self._wait()` 代替 `time.sleep` 即自动获得断点。
- **战斗等原子段内部禁止查暂停**: 原子段内只能用 `time.sleep`。
- **锚点铁律**: 所有业务链以主页为起点, 每个打断点必须能最终回到主页;
  任务终态必须回主页。
- **幂等重跑**: 暂停后处理器重新派发 → 执行器从头重跑;
  游戏状态实时识别保证重跑安全 (已挑战对手置灰跳过),
  任务级进度 (`progress` dict, 如演习 `fought` 计数) 由处理器传入同一对象,
  跨重跑保留。
- **每次执行任务都要有新的上下文**, 任务结束后上下文作废,
  不跨任务留存游戏状态缓存。

### 2.3 代码组织

- 新后端代码并入现有 `autowsgr/` 目录结构, 不创建 `server_v2` 或
  独立 `backend` 目录; 简单功能不得拆散到多个目录。
- 执行器基类: `autowsgr/business/base.py` (`BaseExecutor`)。
- 处理器: `autowsgr/dispatch/processor.py` (`Processor` / `Request` / `TaskPaused`)。
- 注册表: `autowsgr/dispatch/registry.py` — `task_type → 执行器类`,
  业务模块 import 时调用 `register()` 自注册;
  `_TASK_MODULES` 声明 task_type → 模块路径, **延迟 import**
  (避免 dispatch ↔ business 循环依赖)。
- YAML 驱动: `Request.from_yaml(path)` 解析计划 YAML
  (`task_type` 字段确定链路, 其余字段全部作为 params)。
- 老调用方 (scheduler / server / examples / 旧测试) 通过**兼容层**
  (同名 Runner 类内部转调新执行器) 无缝过渡, 待后续统一迁移。

### 2.4 工程规范

- 代码修改四原则: 最小改动、最大复用、最小影响其他功能、最大遵循项目规范。
- 注释要求专业书面语 (禁止口语化); 文件头含算法简介, 类/函数有 docstring。
- 分支: 所有改动在 ShiinaSakuya 分支开发, 合入 ShiinaKuroko 发布;
  禁止未经用户批准创建任何新分支。
- 测试: Dev/Alpha 阶段快速聚焦验证优先 (单个聚焦测试 / 导入检查 /
  真机 E2E), 不设强制 CI 与全量回归。

## 三、当前实现状态

### 3.1 已完成文件

| 文件 | 内容 | 状态 |
|------|------|------|
| `autowsgr/business/base.py` | `BaseExecutor`: `_wait` 断点 / `_check_pause` 暂停协议 / `_report` 事件上报 | 完成 |
| `autowsgr/dispatch/processor.py` | `Processor` (优先级队列 + `interrupt()` 加急 + `run_pending()`) / `Request` (含 `from_yaml`) / `TaskPaused` | 完成 |
| `autowsgr/dispatch/registry.py` | `register()` / `build_executor()` 延迟导入 / `registered_names()`; 已注册: `exercise`, `expedition_check`, `reward_check` | 完成 |
| `autowsgr/business/combat/exercise.py` | `ExerciseExecutor` (见 3.2) + 兼容层 `ExerciseRunner` / `ExerciseOnceRunner` / `run_exercise` | 完成 |
| `autowsgr/business/logistics/expedition.py` | `ExpeditionCheckExecutor`: 主页 → 有通知则 MAP 远征面板收取 → 回主页 | 完成 |
| `autowsgr/business/logistics/reward.py` | `RewardCheckExecutor` (见 3.6) + 兼容层 `collect_rewards` (auto_daily 调用方式不变) | 完成 |
| `autowsgr/ops/reward.py` | 兼容 shim: re-export `RewardCheckExecutor` / `collect_rewards` | 完成 |
| `tools/e2e/cases/reward.py` | 奖励收取 E2E: 处理器路径 + 兼容层路径 (见 3.8) | 完成 |
| `autowsgr/business/combat/fleet_policy.py` | `FleetPolicy` 编队策略查表 (五模式) | 完成 (前序工作) |
| `tools/e2e/cases/exercise.py` | E2E 断点打断用例 (见 3.3) | 完成 |

### 3.2 演习执行器核心逻辑 (`ExerciseExecutor`)

```python
# 基本执行单元: 单场挑战 (含计数 +1)
_fight_one(target):
    选对手 → 确认弹窗 → 准备页选编队 → 船损检测 → 出征 → run_combat
    → progress['fought'] += 1 → 上报 rival_done

# 主流程
_execute():
    导航到演习面板 → _wait (断点①)
    for _ in range(request.count):    # 重复次数 (由入口参数控制, 不写入 YAML)
        while _has_quota():           # 完整模式恒真; 限额模式看计数
            target = _pick_rival()    # 截图识别, 已挑战的置灰自动跳过
            if target is None: break  # 无可挑战对手 → 结束
            _fight_one(target)
            _wait (断点④, 强制检查)
            if not _has_quota(): break
            复位演习面板
    goto_page(MAIN)                   # 锚点: 终态回主页
```

四个断点 (暂停检查内置于 `_wait`):
① `panel_ready` 面板导航完成后; ② `rival_confirmed` 对手确认后 (已进准备页);
③ `fleet_ready` 编队完成后 (尚未出征); ④ `rival_done` 每场战斗完成后 (强制)。
②③ 位于出征准备页 (不在页面注册表/导航图中, 单向中转页): 暂停时先
`go_back` 退回地图页 (含入场动画稳定等待 + 失败重试, 见 `_wait_on_prep`)
再走标准暂停协议 — 直接 `goto_page(MAIN)` 会因准备页被误判为活动页面而
进入活动页浮层关闭死循环 (实机 2026-08-24 修复)。

关键事件流 (GUI/测试可监听): `panel_ready` → (`rival_confirmed` →
`fleet_ready` → `rival_done`) × N → 完成; 暂停时上报 `paused`。

### 3.3 E2E 用例 (`tools/e2e/run.py exercise`)

```bash
# 场景1-4: 在指定断点触发处理器加急 (插入远征检查), 验证打断-恢复
python tools/e2e/run.py --with-ocr exercise --pause-at panel_ready
python tools/e2e/run.py --with-ocr exercise --pause-at rival_confirmed
python tools/e2e/run.py --with-ocr exercise --pause-at fleet_ready
python tools/e2e/run.py --with-ocr exercise --pause-at rival_done

# 场景5: 不打断, 直接跑完并统计计数
python tools/e2e/run.py --with-ocr exercise

# 六段接力 (2026-08-25 新增): 初始化(清弹窗) → 演习四断点各插一次远征检查 → 打完
python tools/e2e/run.py --with-ocr exercise --relay --with-init

# 指定计划 YAML (默认 GUI 系统预设: exercise-队伍2演习.yaml)
python tools/e2e/run.py --with-ocr exercise --yaml <路径>
```

用例内部机制: 事件回调收到目标事件 → `processor.interrupt(远征检查请求)`
→ 演习在最近断点回主页抛 `TaskPaused` → 处理器清信号、重排队 →
远征检查先跑 → 演习重跑 (计数保留)。
断言: 执行流 = `[paused, expedition_check done, exercise done]`、
打断时在主页 (锚点铁律)、累计计数 = 暂停保留 + 重跑场数、终态主页。

### 3.4 实机验证结果

| 场景 | 结果 | 备注 |
|------|------|------|
| 场景4 `rival_done` 打断 | **通过** | 全链路实测: 打完对手1触发打断 → 回主页 → 远征检查收取4支 → 重跑跳过对手1 → 打完2-5 → 计数 1+4=5 |
| 场景1 `panel_ready` 打断 | 协议通过 | 断点触发/回主页/远征检查/重跑全部正确; 当时对手已打光, 重跑识别 [N,N,N,N,N] 空完成 (新语义正确行为) |
| 场景2 `rival_confirmed` | **通过** | 2026-08-24 六段接力 E2E 覆盖 (见下) |
| 场景3 `fleet_ready` | **通过** | 同上 |
| 场景5 不打断跑完 | **通过** | 同上 (接力最后一趟打光全部对手) |
| **六段接力** (初始化+清弹窗 → 四断点各插一次远征检查 → 打完) | **通过** | 2026-08-24 实机一次跑通, 12/12 断言: 执行流 =(paused,done)×4+(done), 四次打断均在主页, 计数 5=1+4, 远征检查 4 次, 终态主页 |

日志存档: `logs/e2e_tools/exercise/<时间戳>/`; 模拟推演
(mock 对手序列) 已验证完整/限额/打断重跑三路径, 见会话记录。

**2026-08-24 实机修复的两个存量问题** (由接力 E2E 暴露):
1. 断点②③ (准备页) 暂停时 `_check_pause` 直接 `goto_page(MAIN)` 会把
   出征准备页误判为活动页面 → 进入活动页浮层关闭死循环 (连点红 X 直至超时)。
   修复: 新增 `_wait_on_prep` — 暂停时先 `go_back` 退回地图页再走标准协议。
2. 准备页入场动画未结束时返回键点击会被吞 (入场后约 1 秒内)。
   修复: `_wait_on_prep` 先等待与正常路径相同的稳定时长, 点击失败重试至多 3 次。

### 3.5 本轮顺手修复的存量问题

1. `dispatch/__init__.py` 引用已不存在的 `registry.resolve` → 重写导出。
2. `dispatch/contract.py` 废弃编排器残留 (TaskChain/Step 旧方案,
   FleetPolicy 已迁至 `business/combat/fleet_policy.py`) → 已删除。
   若发现 `from autowsgr.dispatch import FleetPolicy` 的引用, 改为
   `from autowsgr.business.combat.fleet_policy import FleetPolicy`。
3. `infra/base/ui/pages/tabbed_page.py` 模板目录相对路径在目录迁移后失效
   (`ui/map.png` 找不到) → 改为 `parents[4] / 'data' / 'images' / 'ui'`。
4. `exercise.py` 的 `ConditionFlag` 应从 `autowsgr.types` 导入
   (不在 `autowsgr.combat` 包中)。

### 3.6 任务奖励执行器 (`RewardCheckExecutor`)

- 注册 `task_type = 'reward_check'`, 兼容层 `collect_rewards(ctx)` 原样保留
  (auto_daily 继续调用同一方法, 内部转调新执行器)。
- 流程: 主页 → `MainPage.has_task_ready` 检测任务红点 → 无红点直接返回
  → 有则进任务页 `MissionPage.collect_rewards()` 一键领取 → 回主页。
- 上报事件: `checked` (领取完成, 含 bool 结果)。
- E2E 用例: `python tools/e2e/run.py reward --with-init` (见 3.8)。
- **2026-08-25 存量 bug 修复**: `collect_rewards` 原来在点击「一键领取」后
  **盲点屏幕中央 (640,360)** 关弹窗 — 领取确认弹窗的确认按钮实际在
  (651,502) 且弹窗可能延迟出现: 弹窗未出现时盲点会穿透点到任务行,
  误入活动页面 (实机 E2E 复现: 进入「假日约会」活动页, 页面识别失败,
  导航中止)。修复: 删除盲点点击, 改为模板轮询
  (`Templates.Confirm.all()`, 命中即点确认按钮, 5s 超时) —
  弹窗已出现/延迟出现/未弹窗三种情况都安全; 同时删除
  `dismiss_reward_popup` / `CLICK_CONFIRM_CENTER` / `confirm_center` 死代码。
  实机 E2E 11/11 PASS, 日志确认 `收取=True`。

### 3.7 常量迁移 (infra/base/constants 分类管理)

用户敲定的规则: **初始化/演习/收获奖励三条链路里除时序参数外
(坐标、OCR 参数、颜色等不易更改的值) 全部迁入
`autowsgr/infra/base/constants/` 分类 YAML, 时序参数留在执行器/页面代码**。

分类结构 (数据源 = 目录内 YAML, 文件名 = 页面名, 进程内缓存):

| 分类 | 加载器 | 用途 | 页面文件 |
|------|--------|------|----------|
| `coordinates/` | `point(page,key)` (归一化到 0-1 相对坐标), `points(page,key)` (坐标对列表) | 点击/探测坐标, 1280x720 绝对像素存储 | main, mission, map, exercise, battle_prep, start_screen |
| `colors/` | `color` / `tolerance` / `param` | 颜色 + 容差, 纯阈值 | main, mission, exercise, battle_prep |
| `ocr/` | `param` | OCR 参数与裁切区域 (相对浮点) | mission, battle_prep |
| `signatures/` | `signature` → `PixelSignature.from_dict` | 页面/浮层像素签名 | main, start_screen, battle_prep |

约定与坑:

- 坐标 YAML **禁止携带** color/tolerance 元数据 (用户硬约束);
  颜色一律走 `colors/` 分类, 探测点与配对颜色用同名键呼应。
- 时序常量 (如 `EXERCISE_SWIPE_DELAY`、`PANEL_SWITCH_DELAY`) 不迁移,
  留在原模块并注明"由页面模块管理"。
- 数值换算: 旧相对坐标一律换算为 1280x720 绝对像素整数
  (960x540 分数坐标 ×4/3), 代码侧经 `point()` 归一化后与旧值 ≤1px 误差。
- 迁移后原常量名全部保留 (数据源改为 YAML), 消费者与测试零改动。
- **既有导入顺序敏感**: 先导入 `autowsgr.infra.base.ui.pages.map` 包再导入
  `autowsgr.ui` 会触发循环导入 (map/base.py → ui.utils → ui/__init__ →
  ui/map → infra.map 部分初始化); 正常运行路径 (先 ui 后 infra) 不受影响,
  调试时注意导入顺序。

已迁移批次 (2026-08-25 全部完成, 全量 pytest 通过):

| 批 | 范围 | 状态 |
|----|------|------|
| 1 | 奖励执行器 `RewardCheckExecutor` + 兼容层 | 完成 |
| 2 | 任务页 (mission) 坐标/颜色/OCR 参数 → YAML | 完成 |
| 3 | 主页 (main) 坐标/颜色/签名 + 启动页签名 → YAML | 完成 |
| 4 | 地图页 (map/exercise) + 出征准备页 (battle_prep) 坐标/颜色/OCR/签名 → YAML | 完成 |

### 3.8 奖励收取 E2E 用例 (`tools/e2e/cases/reward.py`)

```bash
# 直接验证 (不初始化)
python tools/e2e/run.py reward

# 先跑初始化链路 (任意状态 → 首页 + 每日浮层清理)
python tools/e2e/run.py reward --with-init
```

验证内容:
1. 处理器路径: 提交 `reward_check` → 执行流 = `[('done', 'reward_check')]`、
   事件流水含 `checked` (且只上报一次)、终态回主页。
2. 兼容层路径: 直接调 `collect_rewards(ctx)` (auto_daily 的调用方式),
   返回 bool, 调用后仍在主页。

无任务红点时执行器在主页空跑返回 (collected=0), 属正常安全行为,
断言不要求本次一定收没收到奖励。实机结果: 2026-08-25 **11/11 PASS**
(初始化 → 一键领取 → 模板确认弹窗 → 回主页, 日志确认 `收取=True`)。

### 3.9 奖励链路双链迁移 (执行器 + 导航器)

用户敲定的架构模式: **所有与奖励相关的功能拆成两条链路** —
① **执行器链路** (business 层): `RewardCheckExecutor` 执行任务;
② **导航器链路** (infra/base/ui): 导航器支撑执行器的执行链路,
页面导航 / 页面识别 / 页面操作等 UI 基础实现全部归属
`autowsgr/infra/base/ui`。执行器不直接持有旧层页面, 一律从 base 取。

2026-08-25 完成状态:

| 链路 | 归属 | 状态 |
|------|------|------|
| 执行器 | `business/logistics/reward.py` (`RewardCheckExecutor` + 兼容层 `collect_rewards`) | 完成 |
| 导航器 — 页面归属 | `infra/base/ui/pages/main_page` (含 `has_task_ready`) + **`infra/base/ui/pages/mission_page` (本次迁入)** | 完成 |
| 导航器 — 导航边 | `infra/base/ui/navigation.py` (`_mission_to_main`) + `main_page/controller.py` (`_get_target_checker`) 均改走 base 路径 | 完成 |

`mission_page` 迁移细节: 主实现 (`data/page/recognition.py`) 从
`autowsgr/ui/mission_page/` 迁入 `autowsgr/infra/base/ui/pages/mission_page/`,
旧目录保留 shim (`autowsgr.ui.mission_page` 继续可用);
导航器与执行器均已改为新路径。验证: 全量 pytest 1008 passed +
reward E2E 11/11 PASS。注意: 与 map 同款**导入顺序敏感**
(先 import infra 页面包再 import `autowsgr.ui` 会循环导入,
先 ui 后 infra 正常, 见 3.7 约定)。

## 四、待办事项 (按优先级)

### 4.1 演习链路收尾

- [x] 实机验证场景 2/3/4/5 及多轮打断: 2026-08-24 六段接力 E2E 一次跑通
      (初始化+清弹窗 → panel_ready/rival_confirmed/fleet_ready/rival_done
      各插一次远征检查 → 打光收尾, 12/12 断言), 用例: `exercise --relay --with-init`。
- [x] 多轮打断稳定性: 接力场景即 4 次连续打断 (含 3 次重跑), 计数与
      锚点铁律全部成立; 另修复准备页暂停导航与入场动画吞点击两个问题。

### 4.2 调度架构推进

- [ ] **server/ (GUI HTTP) 接入处理器**: 当前 `_start_exercise` 等路由
      仍直接调用兼容层 Runner, 需改为构造 `Request` 提交 `Processor`
      (单一处理器实例, GUI 请求经它统一排队/打断)。
- [ ] **cli/ 入口**: 新增后端用户调度入口, 识别用户指令翻译成
      `TaskCommand`; 保留所有原命令兼容。
- [ ] **定时器接入**: `scheduler/daily_plan.py` 的 TimerTrigger 产物
      (远征检查/浴场修理等) 转为 `Request` 走处理器, 替代旧优先级队列。
- [ ] **其他模式迁移**: 按同一骨架迁移战役 (campaign)、普通出征 (normal)、
      决战 (decisive, 保持独立子包); 差异压缩进画像数据, 禁止 if-mode 散弹枪。
- [ ] **任务上下文管理**: 处理器的"查上下文"目前只有优先级 + progress,
      后续需完整的任务状态机 (排队/运行/暂停/完成) 供 GUI 查询。

### 4.3 已知技术债

- `Processor` 为单线程顺序执行模型 (run_pending 跑到队列空);
  GUI 并发请求需外层加锁或改造为常驻调度线程 — 设计待用户确认。
- `interrupt()` 的优先级抬升基于 `_current_priority + 1`,
  并发多次加急的相对顺序未实测。
- 兼容层 Runner 不参与暂停协作 (直调 `executor.run()`),
  迁移 server/scheduler 后应删除。

## 五、快速上手 (新 agent)

```bash
cd c:\ShiinaKuroko\01.Project\AutoWSGR
.venv\Scripts\python.exe -c "from autowsgr.dispatch.registry import registered_names; print(registered_names())"
# 预期: ('exercise', 'expedition_check', 'reward_check')

# 离线逻辑推演 (无需设备)
.venv\Scripts\python.exe -m pytest testing/ -k exercise -x   # 如有相关单测

# 实机 E2E (需模拟器 127.0.0.1:16384 + 游戏就绪)
.venv\Scripts\python.exe tools\e2e\run.py --with-ocr exercise --pause-at rival_done
```

关键阅读顺序: `business/base.py` (执行器契约) →
`dispatch/processor.py` (调度契约) → `business/combat/exercise.py`
(第一个完整实现) → `tools/e2e/cases/exercise.py` (验收方式)。
