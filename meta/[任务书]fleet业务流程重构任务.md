# Fleet 业务流程重构任务书

Task ID: `20260830-autowsgr-upgrade`
Task Status: `done`
Next Step: 无；Fleet 业务流程重构已完成，后续按报告中的边界进行业务联调。

## 一、任务目标

将 `application/ui/controller/fleet/` 重写为一个可由上层稳定调用、内部按业务流程
组织的 UI Controller 域。Fleet 只保留三个一级业务边界：

1. `main_page`：编队/出征准备页面控制器，负责页面 UI 和主流程编排。
2. `formation`：选船核心，负责识别当前编队、解释目标编队规则、计算并执行编队调整。
3. `support`：辅助功能，按补给、战役支援、维修等独立业务能力继续拆分。

最终调用方向：

```text
business / navigation
        ↓
controller.fleet
        ↓
main_page.page 主流程
        ├── formation 选船核心
        └── support 辅助功能
                ↓
common.device / common.ui / common.vision / common.fleet
```

本任务是替代式重写，不保留旧 Fleet 流程兼容。允许迁移阶段暂时破坏尚未接回的旧功能，
但不允许出现语法错误、重复可写状态、静默 fallback、数据破坏或无法解释的依赖环。

## 二、固定工作位置与依据

- Worktree：`C:\ShiinaKuroko\01.Project\AutoWSGR\.worktrees\20260830-autowsgr-upgrade`
- 分支：`codex/20260830-autowsgr-upgrade`
- 目标范围：`autowsgr/application/ui/controller/fleet/`
- 页面样板：`autowsgr/application/ui/controller/operations/sortie_page/battle_page/`
- UI Controller 规范：`meta/[规范]ui-controller-code-style.md`
- 通用规范：`meta/[规范]navigation-code-style.md`

每个执行本任务的 Agent 在第一次写入前必须：

1. 确认 Git 根、当前分支、worktree 绑定和 `git status --short --branch`。
2. 完整读取仓库 `AGENTS.md`、本任务书和两份规范。
3. 读取 `task_plan.md`、`findings.md`、`progress.md`，确认是在续做本任务。
4. 盘点当前阶段涉及的定义、调用方、测试、导航注册、配置和资源。
5. 明确本阶段输入、输出、状态所有者、删除对象和最小验证方式。

## 三、维护者确认的架构决定

### 3.1 三个一级业务边界

`fleet/` 根包文件不视为第四个业务模块。除包入口外，只允许存在：

- 页面控制器 `main_page/`；
- 选船核心 `formation/`；
- 辅助功能 `support/`。

不得重新建立与它们平级的 `workflow/`、`inspection/`、`departure/`、
`shipyard_page/`、`utils/`、`helpers/` 或 `shared/` 杂项目录。

### 3.2 页面控制器是唯一上层业务入口

- 上层业务通过 Fleet 根包取得页面控制器，不直接调用选船核心或辅助功能。
- `main_page/page.py` 同时拥有准备页 UI 原子动作和完整准备流程编排。
- 主流程在文件前部，页面检查、读取、点击、切换和私有辅助在后部。
- 不再增加根 `workflow.py` 作为二次聚合器。

### 3.3 选船核心按真实流程节点拆分

选船核心内部固定为三个节点：

1. 编队识别：从准备页截图得到当前舰名、槽位占用、舰种和等级事实。
2. 编队调整：解释目标规则，确定主选/备选，规划替换、移除和排序，并处理模式差异。
3. 编队选船：进入船池页面，搜索候选，识别船卡，校验约束并完成单舰选择。

三个节点不能通过 Mixin 继承串联，也不能通过页面对象的 `__getattr__` 互相代理。

### 3.4 “YAML 识别”的准确边界

- 原始 YAML 文件读取、语法解析、Schema 校验和业务默认值合并仍由业务/config 入口负责。
- Fleet 不接收 YAML 路径，不读写 YAML 文件，也不复制配置 Schema。
- 编队调整负责理解并执行规范化后的 `FleetSlotRule`、`ShipSelector` 所表达的主选、
  备选、舰种、等级和宽松约束语义。
- `FleetSlotRule`、`ShipSelector` 继续由 `common.fleet` 单独拥有。

### 3.5 辅助功能按业务拥有状态

- `supply`：自动补给状态、快速补给面板和补给流程。
- `campaign_support`：战役支援状态和开关流程。
- `repair`：损伤识别、修理策略、快速维修、复查和手动维修中断。
- 新辅助功能只有在出现真实代码和调用方后才能新增目录。
- 禁止建立横向 `fleet_status` 包收集所有状态；状态由使用它的业务流程拥有。

## 四、破坏性重写授权与硬边界

### 4.1 本任务明确允许

- 删除旧目录、旧类、旧函数、旧导入路径和只验证旧实现的测试。
- 删除全部 Mixin 继承、页面与 Controller 双向代理、动态属性转发和惰性兼容导出。
- 修改 Fleet 公共 API，并同步迁移生产调用方。
- 在阶段迁移期间暂时中断尚未接回的普通、活动、演习、战役或决战功能。
- 删除 `last_changed_fleet` 等旁路状态，改用明确返回值。
- 不为旧测试恢复私有方法、类属性或旧 patch 路径。

### 4.2 即使重写也禁止

- 不得覆盖、reset、stash、checkout、clean 或格式化用户已有工作树修改。
- 不得修改 `bath_page`，也不得顺手治理 Fleet 以外的 Controller。
- 不得降低路径、类型、配置、安全、权限或数据保护校验。
- 不得保留新旧两套可写状态、并行流程或隐式回退。
- 不得使用 `__getattr__`、`__getattribute__`、`sys.modules`、旧包转出、别名类或包装
  函数维持旧流程。
- 不得用宽泛 `except Exception`、无限重试、额外 sleep、批量 `skip/xfail` 或放宽断言
  掩盖迁移缺口。
- 未经用户明确指令，不执行 commit、merge、cherry-pick、push、Tag 或 worktree 清理。

## 五、目标目录结构

```text
fleet/
├── __init__.py                         # Fleet 稳定公共入口
│
├── main_page/                          # 页面控制器
│   ├── __init__.py                     # 导出页面控制器及必要公共类型
│   ├── page.py                         # 主流程在前，准备页 UI 方法在后
│   └── constants.py                    # 准备页坐标、颜色、ROI 和共享静态数据
│
├── formation/                          # 选船核心
│   ├── __init__.py                     # 向 main_page 提供唯一选船核心入口
│   ├── workflow.py                     # 编队识别 -> 调整 -> 选船 -> 复查
│   │
│   ├── fleet_recognition/              # 编队识别节点
│   │   ├── __init__.py
│   │   ├── models.py                   # FleetSnapshot 等跨节点事实模型
│   │   ├── recognition.py              # 舰名、槽位、舰种和等级 OCR
│   │   └── constants.py                # 本节点 OCR/ROI/颜色校准
│   │
│   ├── fleet_adjustment/               # 编队调整节点
│   │   ├── __init__.py
│   │   ├── workflow.py                 # 规划、替换、移除、排序和复查编排
│   │   ├── alignment.py                # 成员集合、槽位清理和顺序调整实现
│   │   ├── rules.py                    # 规范化编队规则的匹配语义
│   │   ├── planning.py                 # 主选优先、备选和槽位分配
│   │   ├── campaign.py                 # 战役固定物理槽位分支
│   │   └── decisive.py                 # 决战无搜索框分支
│   │
│   └── ship_selection/                 # 编队选船节点
│       ├── __init__.py
│       ├── workflow.py                 # 单舰选择或移除流程
│       ├── page.py                     # 船池页面 UI 原子动作
│       ├── recognition.py              # 船卡定位、舰名/舰种/等级 OCR
│       └── constants.py                # 船池坐标、ROI、颜色和滚动校准
│
└── support/                            # 辅助功能
    ├── __init__.py
    ├── supply/
    │   ├── __init__.py
    │   ├── workflow.py                 # 自动补给判断和快速补给流程
    │   ├── recognition.py              # 自动补给状态识别
    │   └── constants.py
    ├── campaign_support/
    │   ├── __init__.py
    │   ├── workflow.py                 # 战役支援检查和切换流程
    │   ├── recognition.py              # 支援开关/耗尽状态识别
    │   └── constants.py
    └── repair/
        ├── __init__.py
        ├── workflow.py                 # 检测、快速维修、复查和中断
        ├── recognition.py              # 血条和损伤状态识别
        └── constants.py
```

这是目标职责图，不是要求机械创建空文件：

- 没有 OCR 的业务包不创建空 `recognition.py`。
- 没有本地校准或共享静态数据的业务包不创建空 `constants.py`。
- `models.py` 仅用于至少两个节点共享的稳定数据契约。
- 模式文件只承载真实差异；通用流程不得复制到 `campaign.py` 或 `decisive.py`。
- 某个文件超过单一业务职责时可以继续按功能拆文件，但不得增加第四个一级边界。

## 六、入口和依赖规则

### 6.1 对外入口

生产业务默认只允许：

```python
from autowsgr.application.ui.controller.fleet import BattlePreparationPage
```

根包可以额外导出稳定的输入/结果类型和明确异常，但不能导出：

- 坐标、颜色、ROI、OCR 参数和页面签名；
- `formation` 或 `support` 的内部函数；
- `FleetChangeController`、Mixin 或算法阶段；
- 以下划线开头的对象；
- 旧路径兼容对象。

导航注册若必须识别船池页面，只允许根包提供一个明确的只读页面检查入口；该例外只供
导航注册使用，业务代码不得借此穿透选船核心。

### 6.2 内部依赖方向

```text
fleet.__init__
      ↓
main_page.page
      ├── formation.__init__ -> formation.workflow
      │       ├── fleet_recognition
      │       └── fleet_adjustment -> ship_selection
      └── support.supply / campaign_support / repair
                              ↓
                            common
```

- `main_page.page` 通过子包入口调用选船核心和辅助流程，不导入私有实现。
- `formation.workflow` 只编排三个选船节点，不复制节点实现。
- `fleet_adjustment` 可以通过显式参数调用页面控制器的公开原子动作；不得运行时反向
  导入 `main_page.page`，类型注解只能放在 `TYPE_CHECKING` 中。
- `ship_selection` 不导入 `fleet_adjustment` 或 `formation.workflow`。
- `support` 不导入 `formation`，也不保存编队流程状态。
- `common` 不得依赖 `application.ui.controller.fleet`。
- 子包之间只通过各自 `__init__.py` 的公开入口调用，不穿透私有函数。

## 七、主流程和子流程契约

### 7.1 页面主流程

`BattlePreparationPage.prepare_and_start_battle(...)` 是本任务的主业务入口：

```text
1. 按 task_type 确认当前准备页
2. 选择目标舰队
3. 调用 formation 完成编队识别与调整
4. 调用 supply 完成补给
5. 仅在战役需要时调用 campaign_support
6. 调用 repair 检查并处理维修
7. 读取最终编队事实
8. 点击开始战斗并确认离开准备页
9. 返回最终 FleetSnapshot
```

页面主流程只描述顺序、模式分支、中断点和终态，不内嵌 OCR 裁剪、规则搜索、船卡
筛选、损伤分类或候选分配算法。

活动和远征准备页差异尚未实机确认时保留明确 TODO，不伪造与普通出征一致的结论。

### 7.2 选船核心流程

`formation.adjust_fleet(...)` 是页面控制器可调用的唯一选船核心入口：

```text
1. fleet_recognition 生成 FleetSnapshot
2. fleet_adjustment 解释 FleetSlotRule 并生成目标分配
3. 已满足时直接返回快照
4. 未满足时由 fleet_adjustment 决定要调整的物理槽位
5. ship_selection 完成一次单舰选择或移除
6. fleet_adjustment 完成成员集合和顺序调整
7. fleet_recognition 复查最终事实
8. 成功返回新 FleetSnapshot，失败抛出明确异常
```

- 不返回含义不明的 `bool`。
- 不通过 `last_changed_fleet` 暂存结果。
- `FleetSnapshot` 是识别事实，不保存重试计数、页面对象或任务进度。
- 普通/活动/演习共用通用搜索流程；战役使用固定物理槽位；决战使用无搜索框流程。

### 7.3 辅助流程

- `supply.apply_supply(page)`：读取自动补给状态，必要时打开快速补给并操作目标槽位。
- `campaign_support.apply_campaign_support(page, enabled)`：读取当前支援状态，只有目标状态
  不一致时切换，并确认结果。
- `repair.apply_repair(page, strategy)`：识别损伤、执行快速维修、有限复查；需要澡堂维修时
  抛出 `ManualRepairRequiredError`，由上层负责导航，不注入跨页面 callback。

## 八、现有定义的目标归属

| 目标位置 | 当前定义或文件 | 重构后的业务职责 |
|---|---|---|
| `main_page/page.py` | `check_current_page`、`read_selected_fleet`、`read_active_panel` | 判断准备页和读取页面自身状态 |
| `main_page/page.py` | `select_fleet`、`select_panel`、`click_ship_slot`、`start_battle`、`try_start_battle`、`go_back` | 准备页原子动作和终态确认 |
| `main_page/page.py` | `prepare_and_start_battle` | 唯一上层主流程 |
| `formation/fleet_recognition` | `_detect.py`、舰名 OCR、槽位占用、等级/舰种 OCR、`FleetSnapshot` | 生成和补全当前编队事实 |
| `formation/fleet_adjustment/rules.py` | `_rules.py` | 解释主选、备选、舰种、等级和宽松规则 |
| `formation/fleet_adjustment/planning.py` | `_planning.py` | 主选优先、全局不重名和目标槽位分配 |
| `formation/fleet_adjustment/workflow.py` | `_alignment.py`、`_change.py` | 替换、补齐、移除、排序、局部修正和最终验证 |
| `formation/fleet_adjustment/campaign.py` | `campaign.py` | 战役固定槽位调整和校验 |
| `formation/fleet_adjustment/decisive.py` | `decisive_fleet.py` | 决战无搜索框调整 |
| `formation/ship_selection` | `_selection.py`、现 `shipyard_page/page.py` | 打开船池、搜索、船卡 OCR、约束校验和单舰选择 |
| `support/supply` | 自动补给检查/切换、快速补给、`apply_supply` | 完成补给子流程 |
| `support/campaign_support` | `check_support_enabled`、`toggle_battle_support` | 完成战役支援子流程 |
| `support/repair` | `detect_ship_damage`、`RepairStrategy`、`check_repair`、`repair_slots`、`apply_quick_repair` | 完成损伤识别和维修子流程 |

需要在 F0 单独判定的旧对象：

- `FleetInfo`、`FleetInfo.to_ships`：若新调用方可直接使用 `FleetSnapshot`，删除而不是兼容。
- `_preferred_ocr`：只保留一种 OCR 后删除切换属性；不得在新模块复制 fallback。
- `check_auto_supply_enabled`、`switch_auto_supply`、`open_quick_supply`：整体迁入 `supply`。
- `open_quick_repair`：迁入 `repair`，通用面板选择仍调用 `main_page` 原子动作。
- `_CardConstraintResult`：归 `ship_selection` 的内部识别/筛选结果，不从包入口导出。
- `BattlePreparationPage.FleetInfo` 类属性及所有私有方法挂载：直接删除。

以下旧机制不迁移：

- `BattlePreparationPage.__getattr__`；
- `FleetChangeController.__getattribute__` 和 `__getattr__`；
- `create_controller`；
- 所有 `*Mixin`；
- `BattlePreparationPage._xxx = ...` 算法挂载；
- 包级惰性 `__getattr__`；
- `last_changed_fleet` 双位置状态；
- 旧目录重导出和旧 patch 路径。

## 九、编码约束

### 9.1 流程和实现分离

- 页面主流程只存在于 `main_page/page.py`；选船核心的节点级总编排只存在于
  `formation/workflow.py`，三个节点可以在自己的 `workflow.py` 编排本节点内部动作。
- 每个节点入口只描述本节点顺序、分支和终态；实现函数放在节点自己的文件中。
- 外部模块只调用根入口；内部主流程只调用子包入口。
- 不新增 Manager、Factory、Registry、EventBus 或只有一个实现的接口。
- 不用十几个 callback 参数模拟对象边界；页面对象作为显式参数传入内部流程即可。

### 9.2 页面文件

- 参考 Battle Page：完整业务流程放在类前部，基础方法和内部辅助放在后部。
- 页面模板/像素状态检查属于 `page.py`；OCR 文本识别属于对应 `recognition.py`。
- `click_*` 只执行原子点击；`open_*`、`select_*`、`try_*` 必须说明并验证终态。
- `go_back` 只执行准备页自身的返回动作；来源页面差异由导航层处理。
- 坐标、ROI、颜色和跨文件共享静态数据放当前业务包 `constants.py`。

### 9.3 OCR、ROI 和规则

- OCR 引擎由运行中的 `GameContext` 提供，不在节点中创建或刷新。
- OCR 专属阈值、采样次数放负责该 OCR 的 `recognition.py` 顶部配置区。
- 点击坐标、OCR/ROI 坐标和颜色统一放同业务包 `constants.py`。
- 纯文本解析与截图读取分开，纯规则函数必须可脱离设备测试。
- 不直接导入 `common.vision.ocr._fuzzy_match` 等私有 API；该兼容问题按既有 OCR 专题处理，
  本重构不得扩散新的私有依赖。

### 9.4 Import 和公开出口

- 使用绝对导入；遵守两份规范当前生效的 `from`、`import` 和禁止语义别名规则。
- 私有对象不得使用 `from module import _name`；导入所属模块后通过模块名调用。
- `__init__.py` 只重导出当前业务包稳定入口和必要类型，不执行设备/OCR/注册副作用。
- 新代码不得导入旧 Fleet 路径，也不得为旧路径创建兼容包。
- 发现循环依赖时先修正职责或改为显式参数，不用延迟导入掩盖。

### 9.5 配置、注释和排序

- 文件顺序遵守：文件说明、import、`TYPE_CHECKING`、日志、顶部配置、类型/class、流程和辅助。
- 文件专属流程参数放本文件首个 `class/def` 前；校准配置集中到所属 `constants.py`。
- 每个配置项说明影响的业务动作和失败边界；不写“等待时间”等无业务语义注释。
- 分区使用业务名称的柱饰条；短文件不添加装饰性分区。
- 类内同样按“主流程在前、辅助方法在后”排列，不按字母机械排序。

### 9.6 状态、结果和异常

- `GameContext` 是运行上下文唯一所有者；Fleet 只保存调用方注入的引用。
- 当前编队事实只有一个 `FleetSnapshot`；不复制影子列表或类属性缓存。
- 成功直接返回明确事实；不可恢复失败抛出具体异常，不返回含义不清的 `False/None`。
- 手动维修只上报需要维修的槽位，不在底层调用澡堂导航。
- 重试必须有限、可解释，并在失败后保留最后一次截图或结构化原因。

## 十、实施阶段

### F0：定义和调用清单冻结

- [x] 枚举 Fleet 内全部 class、def、常量、公开导出、动态挂载和可写状态。
- [x] 为每项记录“保留、重命名、拆分、合并、删除”及唯一目标文件。
- [x] 盘点生产、导航、测试、工具、配置和模板的全部直接消费者。
- [x] 记录每个模式允许暂时失效的范围和后续迁移顺序。
- **门禁**：当前定义数与迁移条目可对账，未分类项为零。
- **Status:** complete

### F1：页面控制器基础

- [x] 将准备页检查、页面状态读取和原子 UI 动作收敛到 `main_page/page.py`。
- [x] 将准备页校准收敛到 `main_page/constants.py`。
- [x] 保留主流程位置但暂不接入尚未完成的子流程。
- [x] 删除 `preparation/` 包和页面对其他能力的转发方法。
- **门禁**：页面检查、舰队/面板读取、原子点击和返回 smoke 通过。
- **Status:** complete

### F2：编队识别节点

- [x] 建立 `formation/fleet_recognition/`。
- [x] 迁移舰名、占用、舰种、等级识别和 `FleetSnapshot`。
- [x] 删除损伤识别和 OCR 引擎 fallback，不混入维修事实。
- [x] 把纯解析和截图识别分开。
- **门禁**：固定截图、纯解析、快照补全和空槽语义测试通过。
- **Status:** complete

### F3：编队选船节点

- [x] 将 `shipyard_page` 和 `_selection.py` 合并进 `formation/ship_selection/`。
- [x] `page.py` 只保留船池页面动作，`recognition.py` 只保留船卡 OCR 和约束识别。
- [x] 将搜索、单舰选择、移除和返回编排放 `workflow.py`。
- [x] 删除 `ChooseShipPage` 旧路径；不新增或扩散私有 OCR 依赖，现有依赖按 OCR 专题处理。
- **门禁**：页面识别、搜索、候选筛选、选择、移除和终态测试通过。
- **Status:** complete

### F4：编队调整节点

- [x] 迁移规则匹配、目标规划、成员集合调整、排序和局部修正。
- [x] 迁移战役固定槽位和决战无搜索框分支，只保留真实差异。
- [x] 删除所有 Mixin、动态代理和页面私有方法挂载。
- [x] 失败改为明确异常，成功返回最终 `FleetSnapshot`。
- **门禁**：主选优先、备选回退、不重名、移除、排序、战役和决战最小测试通过。
- **Status:** complete

### F5：选船核心总流程

- [x] 建立 `formation/workflow.py` 的唯一入口。
- [x] 串联“识别 -> 调整 -> 单舰选择 -> 复查”，不复制节点实现。
- [x] 删除 `FleetChangeController`、`create_controller` 和 `last_changed_fleet`。
- [x] 封闭三个节点的公开出口，禁止页面穿透私有实现。
- **门禁**：替身验证节点顺序、短路、有限重试和最终结果。
- **Status:** complete

### F6：补给辅助流程

- [x] 建立 `support/supply/`，迁移自动补给检查、开关和快速补给。
- [x] 复用 `main_page` 的面板和槽位原子动作，不复制坐标或点击实现。
- [x] 删除原 `main_page/supply/` 和页面转发方法。
- **门禁**：自动补给开/关两条路径和指定槽位补给测试通过。
- **Status:** complete

### F7：战役支援辅助流程

- [x] 建立 `support/campaign_support/`，迁移支援启用、关闭和次数耗尽判断。
- [x] 切换后必须复查目标状态；耗尽状态不得继续点击。
- [x] 从 supply 中删除战役支援职责。
- **门禁**：启用、关闭、耗尽和无需切换四条路径测试通过。
- **Status:** complete

### F8：维修辅助流程

- [x] 建立 `support/repair/`，迁移损伤识别、策略、快速维修和有限复查。
- [x] 删除跨页面手动维修 callback；使用 `ManualRepairRequiredError` 上报槽位。
- [x] 删除原 `fleet_status`、`repair` 包中已迁移定义和重复坐标。
- **门禁**：无损伤、快速维修成功、有限失败和手动维修中断测试通过。
- **Status:** complete

### F9：主流程接入和消费者迁移

- [x] 完成 `prepare_and_start_battle` 的九步页面流程。
- [x] 根 `fleet/__init__.py` 只导出页面控制器和必要公共契约。
- [x] 按演习、普通/活动、战役、决战顺序迁移生产调用方和导航注册。
- [x] 删除所有外部深层导入；不建立旧路径兼容。
- **门禁**：每接入一种模式即运行该模式主链路测试并重读本任务书。
- **Status:** complete

### F10：旧实现删除和最终验收

- [x] 删除全部旧目录、Mixin、代理、动态挂载、旧测试和无消费者 API。
- [x] 扫描私有导入、循环依赖、重复状态、深层生产导入和未迁移定义。
- [x] 运行最终 focused 测试、compileall、import smoke、scoped pre-commit 和 diff 检查。
- [x] 产出综合报告，列明未执行的实机 E2E 和阶段性功能缺口。
- **门禁**：旧路径残留为零，依赖扫描符合第六节方向，定义迁移可完全对账。

## 十一、阶段门禁和检查

每个阶段至少执行：

```powershell
python -m compileall -q autowsgr/application/ui/controller/fleet
uv run --locked python -c "import autowsgr.application.ui.controller.fleet"
git diff --check
```

按阶段补充最小行为验证：

- 页面阶段：页面签名、页面状态、原子动作和终态等待。
- 识别阶段：纯解析、固定截图、ROI 和快照字段。
- 规则阶段：主选、备选、唯一性、等级/舰种边界和模式分支。
- 选船阶段：搜索、滚动、候选筛选、点击、移除和退出页面。
- 辅助阶段：状态一致、无需操作、成功操作和明确失败。
- 调用方阶段：对应模式业务链路，不要求旧 API 测试继续通过。

受影响文件使用 scoped pre-commit；工作树存在大量其他修改时不得运行可能改写全仓的
`pre-commit run --all-files`。不得使用 `git add .`。

旧测试处理规则：

1. 仍验证有效业务行为：迁移到新入口和新所属模块。
2. 只验证旧导入、Mixin、代理、动态挂载或私有方法：删除。
3. 暴露真实新流程错误：修复根因并保留最小回归检查。
4. 不使用兼容包装让旧测试重新变绿。

## 十二、强制重读协议

每完成 F0-F10 的任一阶段，必须执行：

```powershell
Get-Content -Raw -Encoding UTF8 -LiteralPath 'C:\ShiinaKuroko\01.Project\AutoWSGR\.worktrees\20260830-autowsgr-upgrade\meta\[任务书]fleet业务流程重构任务.md'
```

重读后才能进入下一阶段。若任务书、实际代码、两份规范或维护者最新决定冲突，立即停止
当前阶段，先更新任务书并记录冲突，不得沿旧计划继续。

## 十三、最终交付物

- 只含 `main_page`、`formation`、`support` 三个一级业务边界的新 Fleet 模块。
- 页面控制器唯一上层入口和完整准备流程。
- 编队识别、编队调整、编队选船三个独立选船节点。
- 补给、战役支援、维修三个独立辅助流程。
- 全部定义和调用方迁移对账结果。
- focused 测试、compileall、import smoke、scoped pre-commit 和 diff 检查记录。
- 综合报告：删除项、暂时失效功能、未执行验证、已知风险和后续业务层联调事项。
