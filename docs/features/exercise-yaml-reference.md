
# AutoWSGR 演习 YAML 完整参考

本文从 AutoWSGR 的 ShiinaKuroko 分支源码、现有 YAML、普通战计划模型、演习执行器和 API DTO 中重新整理演习 YAML 契约。

目标：

- 使用明确的 task_type 声明任务类型。
- 使用 fleet_id 选择 1-4 号编队。
- 使用 formation 直接表达阵型策略，不重复定义 formation_strategy。
- 使用 fleet 或 fleet_presets 表达编队详情。
- 使用 night 表达夜战策略。
- 使用 sl_when_failed 表达演习失败后的统一 SL 开关。
- 预留 enemy_rules 和 enemy_formation_rules 对手判断能力。

## 一、最终推荐格式

~~~yaml
task_type: exercise

fleet_id: 2
formation: 2

fleet:
  - 舰船 A
  - 舰船 B
  - 舰船 C
  - 舰船 D
  - 舰船 E
  - 舰船 F

night: false
sl_when_failed: false

# 预留：根据对手舰种和数量判断
enemy_rules: []

# 预留：根据对手阵型判断
enemy_formation_rules: []
~~~

高级编队可以把 fleet 替换为 fleet_presets：

~~~yaml
task_type: exercise

fleet_id: 2
formation: 2

fleet_presets:
  - name: 主力
    ships:
      - name: U-47
        candidates: [U-96, U-81]
        ship_type: ss
        min_level: 80
        max_level: 110
        relaxed: false

night: true
sl_when_failed: true
enemy_rules: []
enemy_formation_rules: []
~~~

不定义 formation_strategy 或 night_strategy：

- formation 已经表示阵型策略，取值为 1-5。
- night 已经表示夜战策略，取值为 true/false。
- 动态阵型通过 enemy_rules 或 enemy_formation_rules 扩展。

## 二、当前演习执行链

当前演习没有独立的 YAML 加载器，实际执行链如下：

~~~text
usersettings.yaml
  -> DailyAutomationConfig
  -> build_daily_plan()
  -> ExerciseOnceRunner
  -> ExerciseRunner(fleet_id)
  -> BattlePreparationPage.select_fleet()
  -> CombatPlan(mode=EXERCISE)
  -> run_combat()
  -> CombatHandler
~~~

当前模块职责：

| 模块 | 当前职责 |
|---|---|
| autowsgr/infra/config.py | 用户配置、日常配置、通用战斗配置 |
| autowsgr/scheduler/daily_plan.py | 注册自动演习任务 |
| autowsgr/ops/exercise.py | 选择对手、选择舰队、启动演习 |
| autowsgr/combat/plan.py | 战斗计划和节点策略 |
| autowsgr/combat/fleet.py | 固定舰队和智能舰队规则 |
| autowsgr/combat/rules.py | 对手规则解析 |
| autowsgr/combat/handlers.py | 阵型、夜战、规则和 SL 执行 |
| autowsgr/server/schemas.py | API 演习请求，不是 YAML |
| autowsgr/server/routes/task.py | API 演习任务启动 |

当前 ExerciseRunner 只接收舰队编号，然后调用 BattlePreparationPage.select_fleet()。

当前演习战斗参数在 autowsgr/ops/exercise.py 中硬编码为：

~~~python
NodeDecision(
    formation=Formation.single_column,
    night=True,
)
~~~

因此新的演习 YAML 需要让 ExerciseRunner 接收完整的演习计划，而不是只接收 fleet_id。

## 三、字段状态总表

| 字段 | 当前是否存在 | 当前来源 | 当前消费 | 新演习格式 |
|---|---|---|---|---|
| task_type | 否 | API 只有 type: exercise | 没有 YAML 消费者 | 新增 |
| fleet_id | 是 | 普通计划 YAML、API、演习参数 | 普通战和演习代码使用 | 复用 |
| formation | 是 | 普通计划节点字段 | 普通战消费，演习硬编码 | 提升到演习顶层 |
| fleet | 是 | 普通计划顶层字段 | 普通战消费，演习不消费 | 复用并接入演习 |
| fleet_presets | 是 | 普通计划顶层字段 | fleet.py 消费，演习不消费 | 可选复用并接入演习 |
| night | 是 | 普通计划节点字段 | 普通战消费，演习硬编码为 true | 提升到演习顶层 |
| sl_when_failed | 否 | 无统一字段 | 没有统一演习失败开关 | 新增 |
| enemy_rules | 是 | 普通计划节点字段 | 普通战消费，演习不消费 | 复用并新增演习消费 |
| enemy_formation_rules | 是 | 普通计划节点字段 | 普通战消费，演习不消费 | 复用并新增演习消费 |

## 四、演习 YAML 字段定义

### 4.1 task_type

状态：新增。

~~~yaml
task_type: exercise
~~~

含义：声明当前文件是演习任务。

建议约束：

- 必须存在。
- 唯一允许值为 exercise。
- 其他任务类型在加载阶段拒绝。
- API 的 type: exercise 在边界处转换为 YAML 的 task_type。

当前不存在 YAML 消费模块，需要新增演习 YAML 加载器或统一任务加载器。

### 4.2 fleet_id

状态：复用现有字段名。

~~~yaml
fleet_id: 2
~~~

含义：选择第几编队。

当前消费：

| 来源 | 消费模块 |
|---|---|
| 普通计划 YAML | CombatPlan.from_dict() |
| 普通战运行 | resolve_fleet_selection()、NormalFightRunner |
| 演习代码参数 | ExerciseRunner、BattlePreparationPage.select_fleet() |
| API | ExerciseRequest、_start_exercise() |

目标取值为 1、2、3、4。

现有 API 校验范围是 1-6，ExerciseRunner 本身没有范围校验。新的 YAML 契约应明确采用 1-4。

### 4.3 formation

状态：复用现有字段名，但改变 YAML 所在层级。

~~~yaml
formation: 2
~~~

含义：默认阵型，也是当前框架中的阵型策略。

| 值 | 阵型 |
|---|---|
| 1 | 单纵阵 |
| 2 | 复纵阵 |
| 3 | 轮型阵 |
| 4 | 梯形阵 |
| 5 | 单横阵 |

普通战消费链：

~~~text
node_defaults.formation / node_args.<node>.formation
  -> NodeConfig
  -> NodeDecision
  -> CombatHandler
~~~

演习当前固定使用单纵阵。新的演习执行器需要把 YAML 的 formation 转成 NodeDecision。

不再新增 formation_strategy。

### 4.4 fleet

状态：复用现有字段名。

~~~yaml
fleet:
  - 舰船 A
  - 舰船 B
  - 舰船 C
  - 舰船 D
  - 舰船 E
  - 舰船 F
~~~

含义：按物理槽位描述固定编队。

普通战消费链：

~~~text
CombatPlan.from_yaml()
  -> CombatPlan.fleet
  -> resolve_fleet_selection()
  -> NormalFightRunner
~~~

演习当前只选择 fleet_id，不读取 fleet。新的演习准备流程需要把舰船名称转换为逐槽选船操作。

建议约束：

- 演习最多使用 6 个槽位。
- 每个槽位为舰船名称字符串。
- fleet 和 fleet_presets 建议二选一。
- 是否允许空槽需要由演习业务明确。

### 4.5 fleet_presets

状态：复用现有高级字段，可选。

~~~yaml
fleet_presets:
  - name: 主力
    ships:
      - name: U-47
        candidates:
          - U-96
          - U-81
        ship_type: ss
        min_level: 80
        max_level: 110
        relaxed: false
~~~

字段含义：

| 字段 | 含义 |
|---|---|
| name | 预设名称 |
| ships | 非空槽位列表 |
| ships[].name | 槽位主选舰船 |
| ships[].candidates | 按顺序尝试的备选舰船 |
| ships[].search_name | OCR/搜索名称 |
| ships[].ship_type | 舰种代码 |
| ships[].min_level | 最低等级，必须 >= 1 |
| ships[].max_level | 最高等级，必须 >= min_level |
| ships[].relaxed | 是否放宽严格匹配，默认 false |

当前消费模块：

- autowsgr/combat/fleet.py
- fleet_slot_from_yaml()
- fleet_presets_from_yaml()
- resolve_fleet_selection()

演习需要复用这些转换函数，不要重新实现舰队规则解析器。

### 4.6 night

状态：复用现有字段名，但改变 YAML 所在层级。

~~~yaml
night: false
~~~

含义：是否在夜战提示页选择追击夜战。

| 值 | 行为 |
|---|---|
| true | 进入夜战 |
| false | 不进入夜战 |

普通战消费链：

~~~text
NodeConfig.night
  -> NodeDecision.night
  -> CombatHandler._handle_night_prompt()
  -> click_night_battle()
~~~

演习当前固定为 night=true。新的演习 YAML 应覆盖该硬编码。

第一版建议默认 false，并要求任务显式填写。

不新增 night_strategy。

### 4.7 sl_when_failed

状态：新增。

~~~yaml
sl_when_failed: false
~~~

含义：本场演习战斗失败后是否执行 SL。

建议约束：

- 类型为 bool。
- 默认值为 false。
- 由演习级失败结果处理逻辑消费。
- 明确哪些 CombatResult.flag 属于可 SL 失败。
- 不使用宽泛异常吞掉方式实现。

普通战已有三个阶段性 SL 字段：

| 已有字段 | 当前含义 | 当前消费位置 |
|---|---|---|
| SL_when_spot_enemy_fails | 索敌失败是否 SL | combat/handlers.py |
| SL_when_detour_fails | 迂回失败是否 SL | combat/handlers.py |
| SL_when_enter_fight | 进入战斗时是否 SL | combat/handlers.py |

这三个字段不能直接替代演习统一失败开关。

### 4.8 enemy_rules

状态：复用现有字段名，演习消费逻辑新增。

~~~yaml
enemy_rules:
  - ["CV > 0", retreat]
  - ["SS >= 3", detour]
  - ["BB >= 2", 4]
~~~

含义：根据对手舰种和数量决定动作。

支持：

- >、>=、<、<=、==、!=
- and
- 舰种求和，例如 CL + DD >= 2
- retreat：撤退
- detour：迂回
- 1-5：选择我方阵型

不支持 or，需要拆成多条规则。

普通战消费链：

~~~text
NodeConfig.enemy_rules
  -> NodeDecision.from_node_config()
  -> RuleEngine.from_legacy_rules()
  -> CombatHandler
~~~

演习当前没有把对手编成交给规则引擎，需要新增演习适配。

### 4.9 enemy_formation_rules

状态：复用现有字段名，演习消费逻辑新增。

~~~yaml
enemy_formation_rules:
  - ["单纵阵", retreat]
  - ["复纵阵", 2]
~~~

含义：根据对手阵型决定撤退、迂回或我方阵型。

普通战消费链：

~~~text
NodeConfig.enemy_formation_rules
  -> NodeDecision.from_node_config()
  -> RuleEngine.from_formation_rules()
  -> CombatHandler
~~~

普通战中，阵型规则优先于普通 enemy_rules。演习需要新增对手阵型识别结果到该规则引擎的连接。

## 五、相关但不放入第一版演习 YAML 的字段

### 普通 CombatPlan 顶层字段

普通/活动战计划解析器还读取：

| 字段 | 第一版演习 | 原因 |
|---|---|---|
| mode | 否 | 演习由 task_type 推导为 EXERCISE |
| chapter | 否 | 演习没有普通地图章节 |
| map | 否 | 演习没有普通地图编号 |
| event | 否 | 活动地图专用 |
| fleet_id | 是 | 编队选择 |
| fleet | 是 | 编队详情 |
| fleet_presets | 可选 | 智能编队详情 |
| repair_mode | 暂不放入 | 当前演习没有 YAML 修理流程 |
| fight_condition | 暂不放入 | 演习没有普通战出征战况选择 |
| selected_nodes | 否 | 演习没有普通地图节点 |
| node_defaults | 否 | 第一版使用顶层字段 |
| node_args | 否 | 第一版没有节点级配置 |
| name | 否 | 文件名和 task_type 已足够 |

### ExerciseConfig 代码字段

ExerciseConfig 定义了以下代码字段，但它们不是现有演习 YAML 字段：

| 字段 | 当前是否被 YAML 消费 | 处理建议 |
|---|---|---|
| fleet_id | 否 | 映射到新的 fleet_id |
| selected_nodes | 否 | 第一版不放入 |
| discard | 否 | 如果需要，新增 YAML 字段 |
| exercise_times | 否 | 如果需要，新增 YAML 字段 |
| robot | 否 | 如果需要，新增 YAML 字段 |
| max_refresh_times | 否 | 如果需要，新增 YAML 字段 |

## 六、推荐的严格契约

第一版只允许以下顶层键：

~~~text
task_type
fleet_id
formation
fleet
fleet_presets
night
sl_when_failed
enemy_rules
enemy_formation_rules
~~~

建议约束：

| 约束 | 建议 |
|---|---|
| task_type | 必须为 exercise |
| fleet_id | 1-4 |
| formation | 1-5 |
| fleet/fleet_presets | 二选一 |
| fleet | 最多 6 个槽位 |
| night | bool，建议显式填写 |
| sl_when_failed | bool，默认 false |
| enemy_rules | list，默认 [] |
| enemy_formation_rules | list，默认 [] |
| 未知字段 | 加载时拒绝，不要静默忽略 |

## 七、目标消费链

~~~text
ExercisePlan.from_yaml()
  -> 校验 task_type
  -> 解析 fleet / fleet_presets
  -> 构造 ResolvedFleetSelection
  -> 构造 CombatPlan(mode=EXERCISE)
  -> 设置 formation
  -> 设置 night
  -> 设置 enemy_rules
  -> 设置 enemy_formation_rules
  -> ExerciseRunner(ctx, plan)
  -> BattlePreparationPage
  -> CombatHandler
  -> 按 sl_when_failed 处理失败
~~~

建议把 ExerciseRunner 从：

~~~python
ExerciseRunner(ctx, fleet_id)
~~~

调整为：

~~~python
ExerciseRunner(ctx, exercise_plan)
~~~

这样演习执行器才能消费完整 YAML，而不是继续硬编码阵型、夜战和舰队详情。

## 八、源码索引

| 文件 | 关键内容 |
|---|---|
| autowsgr/ops/exercise.py | 当前演习执行器、舰队选择、硬编码阵型和夜战 |
| autowsgr/infra/config.py | DailyAutomationConfig、ExerciseConfig、NodeConfig |
| autowsgr/scheduler/daily_plan.py | auto_exercise 和 exercise_fleet_id |
| autowsgr/combat/plan.py | CombatPlan、NodeDecision、计划解析 |
| autowsgr/combat/fleet.py | fleet、fleet_presets 和舰队选择 |
| autowsgr/combat/rules.py | 对手规则解析 |
| autowsgr/combat/handlers.py | 阵型、夜战、规则和 SL 消费 |
| autowsgr/server/schemas.py | API ExerciseRequest |
| autowsgr/server/routes/task.py | API 演习启动 |
