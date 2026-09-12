# infra 拆分为 application/common 迁移任务书

> 用途：交给后续 Agent 执行的架构迁移任务书。
>
> 目标仓库：AutoWSGR backend，目标包根目录为 autowsgr/。
>
> 本任务只新增本任务书，不代表当前审查 Agent 直接修改 backend 实现。

## 0. 任务目标与边界

将当前混合在 infra、ui、combat 以及部分 business 中的能力，按最新用户决定拆成两个与 business 同级的 Python 包：

- autowsgr/application/
- autowsgr/common/

这两个目录必须作为 Python package 交付，至少包含：

- autowsgr/application/__init__.py
- autowsgr/common/__init__.py

用户口中的“新增两个文件”按后续定义理解为“新增两个同级文件夹/包”，不是创建没有扩展名的普通文件。

交接时的 backend 基线中这两个目录已经以空目录形式存在，但尚无 __init__.py、已跟踪实现或可复用 API；Checkpoint 1 负责把它们补齐为正式 package，不要把空目录误判成迁移已完成。

目标依赖方向：

~~~text
server -> dispatch -> business -> application -> common
~~~

其中：

- server/dispatch 是上层入口和调度，不得绕过 business 直接调用 application 的业务入口。
- business 持有业务用例、领域规则、业务状态和业务结果；可以引用下层，必要时引用同层业务模块。
- application 持有被 business 调用的公共应用能力，例如 combat engine、action、UI 语义导航器；只能依赖 common（另加标准库和必要的底层第三方库）。
- common 持有不再依赖更高层的超级基础能力，例如 OCR 实现、OpenCV2 识别原语、设备连接、截图、低层点击/等待和资源加载；不得依赖 application、business、dispatch、server 或旧 infra 业务代码。

## 1. 用户架构定义（原文）

以下内容是本任务的硬性架构定义，后续 Agent 不得用旧架构笔记覆盖或解释掉：

~~~text
infra，需要再拆分成两层
 - application
 - common
这两个文件夹，和business同级形成：
 - business：这里定义不变，就是业务实现，只能互相引用或者引用下层
 - application：这里放被上层 business 引用的公共方法，只能引用common，比如combat engine、action。ui的导航器
 - common ： 这里是无法再有依赖的超级基础方法，比如OCR实现、opencv2识别、设备连接、导航器的引用点击等等

原则：确保application层级的方法只能通过入口被上层引用，入口下可以挂载同一业务域内的子方法，并且使用子方法依赖下层common，形成垂直结构
~~~

本次目录含义以此定义为准。尤其不要把目标误解成 autowsgr/infra/application 或 autowsgr/infra/common；用户要求的是 autowsgr/application 和 autowsgr/common，它们与 autowsgr/business 同级。

## 2. 审查发现（原文，禁止改写）

以下区块原封不动保留审查发现，执行时必须逐条关闭或记录明确的延期理由：

- infra/combat 同时混合战斗引擎、领域模型、规则、结果模型和页面适配。
- infra/ui/pages/.../fleet_change 中 _planning.py、_rules.py 是纯算法，却位于 UI 层。
- infra/ui/pages/battle_preparation/repair.py 反向导入 business。
- types.py、map/data.py、recognition.py、choose_ship.py、ui/decisive/* 等仍有大量坐标、ROI、颜色和签名硬编码。
- 模板入口存在 TemplateKey、CombatTemplates、Templates.FightResult 等重复来源。
- GameContext 同时持有基础设施、游戏状态、每日计数器和停止信号。
- infra/ui/navigation/service.py 实际是语义导航，却仍位于 infra。
- LOOT_MAX、SHIP_MAX、战果等级顺序等游戏规则不应迁移到通用基层。
- HTTP fight_condition 存在裸 int 传入 CombatPlan、下游按枚举访问的契约风险。
- 当前未提交的舰名 alias 功能存在空值静默丢弃和全局状态污染风险。
- 已确认最新 E2E 日志 logs/e2e_tools/exercise/20260830_220134 支持“5 个对手、5 个断点、战斗成功”的记录。

“原文”区块不可被改写成只有结论的摘要。可以在后文追加定位、影响、方案和验收证据，但不能删除上述句子或把问题改成无责任归属的泛化表述。

## 3. 强制规则

### 3.1 依赖规则

新代码必须遵守以下规则：

~~~text
common:
  允许：标准库、底层第三方库、common 内同层/下层技术模块
  禁止：application、business、dispatch、server、旧 infra 中的业务实现

application:
  允许：标准库、必要的底层第三方库、common
  禁止：business、dispatch、server、旧 infra 业务实现

business:
  允许：同域 business、application、common
  禁止：server、dispatch；禁止把 infra 当作新实现来源

dispatch/server:
  只通过 business 用例入口使用业务能力
~~~

“只能引用 common”指 application 对项目内分层包的依赖；标准库和必要的底层第三方依赖不属于上层项目包依赖。common 也不能因为需要类型标注而反向导入业务类型，应使用标准库 Protocol、基础数据类型或 common 自有类型。

application 的公开入口必须少而明确。入口可以在同一业务域下挂载私有/内部子方法，但调用链必须呈现为：

~~~text
business/combat/<use_case>
  -> application/combat/<entry>
    -> application/combat/<sub_action>
      -> common/device | common/vision | common/ui
~~~

不得出现以下绕过：

~~~text
business -> application/submodule/internal  # 绕过 application 入口
dispatch -> application                   # 绕过 business
common -> business/application             # 反向依赖
business -> infra 的真实实现              # 继续扩大旧边界
~~~

### 3.2 不得把业务规则下沉到 common

下列内容是游戏业务语义，不因“看起来像常量”就移动到 common：

- LOOT_MAX、SHIP_MAX。
- 战果等级的业务顺序和等级判断。
- 出征/演习/战役/决战的次数、停止条件和策略。
- 舰队编成约束、舰种/等级规则、对手选择规则。
- 任务进度、每日计数器、暂停/停止意图和业务结果。

common 只处理“如何截图、如何裁切、如何识别像素/模板、如何点击/等待、如何连接设备”。application 负责把这些技术能力组成可复用动作；business 决定“何时调用、调用什么、失败意味着什么”。

### 3.3 兼容和变更纪律

- 开始前记录当前 Git SHA、分支、dirty diff 和未跟踪文件；不得 reset、checkout、stash、覆盖或整理不属于本任务的修改。
- 不做全仓库无差别重命名。每次移动前搜索定义、全部调用方、导入方、测试和资源契约。
- 旧路径如暂时保留，只能是薄 shim/re-export；不得复制实现，也不得让新代码继续引用 shim。
- 不创建 infra/base、infra/common、infra/base/combat 等新的重复层。
- 不因测试方便把生产用的调试开关、测试状态或全局可写 alias 暴露给业务。
- 发现 API、YAML、GUI/backend DTO 或行为语义需要改变时，先停在当前 checkpoint，记录现状、提议、影响和验证方式；不要暗中扩展范围。
- 本任务不追加真实设备 E2E。当前记录已经使用 5/5 次实机预算，后续只能使用静态测试、单元测试、导入检查、截图/日志既有证据和必要的模拟对象。

## 4. 发现问题的处理建议

### 4.1 infra/combat 的拆分

建议按职责而不是按文件名迁移：

| 当前能力 | 推荐归属 | 说明 |
|---|---|---|
| CombatEngine 的流程编排、通用 action 组合 | application/combat | 形成少量公开入口；不持有战役/演习业务规则 |
| 页面点击、等待、截图、识别调用 | application/ui 与 common/ui、common/vision | application 组合动作，common 执行物理/识别原语 |
| CombatPlan 的游戏类型、路线、战果语义 | business/combat | 属于领域模型和业务输入，不下沉到 common |
| 战斗规则、次数、停止条件、结果解释 | business/combat | 业务策略和结果归属保持在 business |
| 原始 ROI、PixelRule、模板匹配、OpenCV/ OCR 处理 | common/vision 或 common/calibration | 只保留技术识别，不解释业务结果 |
| 战斗历史事件若表达业务事件 | business/combat | 如果只是底层识别事件，先转成 common 的技术结果再由 business 解释 |

迁移后，application/combat 的入口不能导入 business。需要使用业务输入时，由 business 在边界处转换为 application 自有的、依赖中立的请求对象或基础参数。

### 4.2 fleet_change 的算法和 UI

_planning.py、_rules.py 虽然是纯函数/纯算法，但“舰队选择规则”本身包含游戏领域语义，不能仅因为它们不点击屏幕就放入 common。

推荐处理：

- 舰种、等级、主选/备选、重复舰船、槽位和严格/宽松校验等规则移到 business/combat/fleet。
- 选择结果的 YAML/API 解析在业务边界完成。
- 页面上的查找、滚动、OCR 读卡、点击替换和最终 UI 校验由 application/ui/battle_preparation 组合。
- OCR、ROI、图像裁切和模板/像素原语由 common/vision 提供。
- 若某个纯算法确实不含任何游戏语义、且有多个应用域复用，才可放 application；不得直接放 common。

### 4.3 repair 的反向依赖

当前 repair.py 反向导入 business，说明页面层和业务策略混在一个对象中。推荐拆成：

~~~text
business/logistics/repair
  -> application/ui/battle_preparation/repair_action
    -> common/ui + common/vision + common/device
~~~

页面 action 只负责完成物理操作并返回可验证的技术结果；快速修理策略、浴室修理业务、黑名单和停止条件留在 business。旧 RepairMixin 如需要兼容，只能薄委托到新 application action，不能在 shim 中重新实现策略。

### 4.4 语义导航和低层点击

infra/ui/navigation/service.py 的语义 Navigator 应迁到 application/ui/navigation：

- application Navigator 持有页面语义、目标锚点、路由执行和稳定性确认。
- common/ui 只提供引用点击、等待、页面/像素/模板探测等低层能力。
- Navigator 不拥有 TaskInstance、任务队列、下一任务选择或业务停止条件。
- 任务之间是否交接由 dispatch 决定；一个业务内部需要到哪个页面由 business 声明，路径如何走由 application Navigator 执行。
- 不在 dispatch 和 business 各复制一套 Navigator。

### 4.5 GameContext 和状态所有权

GameContext 同时持有基础设施、游戏状态、每日计数器和停止信号，不能整体下沉到 common。推荐拆分：

- 设备/OCR/UIProfile 等资源句柄：由 common 提供能力，必要的资源生命周期由 application/runtime 组装。
- 页面导航会话状态：由 application Navigator 自己持有。
- 任务暂停、停止、队列和 ExecutionAttempt：由 dispatch 持有。
- 游戏快照、舰队和业务进度：由对应 business 用例或任务级状态持有。
- 每日计数器和停止规则：由 business/dispatch 按实际所有权持有。
- 一个运行时资源只能有一个权威 owner；不要用第二个全局 context 复制状态。

如果本次迁移不能一次拆完，必须先建立兼容 facade，并在 findings/progress 中写出剩余字段、唯一 owner、消费者和删除条件；不能把混合 GameContext 原样复制到 common。

## 5. 本地常量、校准值和模板的迁移判据

### 5.1 判定表

| 常量类型 | 推荐位置 | 是否下沉 common | 判定 |
|---|---|---:|---|
| 设备键值、连接参数、截图/点击/等待的技术默认值 | common/device 或 common/system | 是 | 不含游戏语义，且由底层能力解释 |
| OCR 引擎参数、OpenCV kernel、像素颜色阈值、原始 ROI、PixelSignature、模板文件标识 | common/vision 或 common/calibration | 是 | 只表达识别技术和校准数据 |
| 跨页面的物理点击点、低层返回/关闭/确认点击 | common/ui 或 common/calibration | 通常是 | 需要确认坐标含义和调用方；共享值合并，页面专属值按域隔离 |
| 页面语义导航目标、页面转移和安全断点 | application/ui/navigation | 否 | 不是单纯点击，而是应用能力 |
| 舰队槽位、舰种、等级、路线、战果等级和每日上限 | business | 否 | 业务规则 |
| 通用 action 的重试次数、等待节奏 | application | 视情况 | 只有在技术动作的通用安全策略时下沉；业务停止/次数不得下沉 |
| task 状态、计数器、暂停/停止信号 | dispatch/business | 否 | 这是可变状态，不是 common 常量 |
| 只被一个业务使用、且值表达业务选择的默认值 | business | 否 | 留在业务域并命名清楚 |
| 测试专属样本、断言阈值和 fixture 数据 | testing | 否 | 不进入生产 common |

“能迁移到基层”必须同时满足：没有业务语义、没有上层导入、调用方可追踪、迁移后有唯一来源。仅仅把局部变量改成大写或搬到 constants.py 不算完成。

### 5.2 本次审查确认需要逐项处理的硬编码

以下文件/类别必须建立迁移清单，逐项填写“原位置、名称、含义、调用方、目标、是否保留、验证证据”：

- autowsgr/types.py：混合的技术类型、页面枚举和业务枚举，不能整体搬迁；按语义拆分。
- autowsgr/infra/ui/pages/map/data.py：页面坐标、探测颜色以及地图/任务语义混在一起；物理校准和业务枚举分离。
- autowsgr/infra/combat/recognition.py：敌舰扫描区、编队 ROI、结算页识别点和页面签名；扫描区/ROI/签名下沉 common，战斗阶段解释留在 business/application。
- autowsgr/infra/combat/recognizer.py：阶段签名、结果模板入口和识别映射；底层模板/像素规则单一归 common，战果含义单一归 business。
- autowsgr/infra/combat/node_tracker.py：节点探测的颜色和采样点；识别原语下沉 common，节点选择规则留在 business。
- autowsgr/infra/ui/pages/battle_preparation/ 与 fleet_change/：槽位、OCR 裁切、滚动/点击坐标和编队规则；坐标/ROI/识别参数下沉 common，舰队规则留 business，页面动作归 application。
- autowsgr/ui/decisive/overlay.py、map_controller.py、fleet_ocr.py、battle_page.py：PixelRule、HSV 范围、ROI、模板、颜色和内联点击；原始视觉/坐标下沉 common，决战章节/推进/退出等语义留 business/application。
- autowsgr/infra/ui/pages/map/panels/sortie.py：局部探测点、MAX_MISSES、MAX_STUCK、导航等待和重试；物理探测参数归 common/application，流程安全和业务停止规则不得误下沉。
- autowsgr/infra/fleet/policy.py、autowsgr/infra/fleet/model.py：舰队范围、覆盖策略和选择模式；这是舰队业务规则，迁移到 business/combat/fleet，不是 common。

参考底稿为 update/coordinates-inventory.md。该清单中的坐标可作为迁移输入，但不能绕过调用方审计直接批量复制。

坐标资源继续遵守以下边界：

- 坐标资源只有坐标数据；不要把流程、业务规则、颜色容差或状态机塞进 YAML。
- 颜色、ROI、签名和模板元数据按现有资源组织，必要时由 common loader 统一读取。
- 相对坐标和绝对坐标的换算必须保持现有运行语义；敌舰扫描区和截图 resize 必须成对验证。
- 估计值、未实机确认值必须显式标记，不能在迁移中伪装成已校准值。

### 5.3 模板的唯一来源

TemplateKey、CombatTemplates、Templates.FightResult 等重复入口必须先画出定义/调用图，再选择唯一 canonical source：

- common 只提供原始模板标识、资源加载和匹配结果。
- application 组合匹配动作，不复制模板字典。
- business 将匹配结果解释为 FightResult 或其他业务结果。
- 旧入口可以短期 re-export canonical source；任何新调用只能指向唯一来源。

## 6. 强参考迁移矩阵

下表是推荐落点，不是允许跳过调用图审计的机械重命名方案。若 Agent 选择不同落点，必须在 checkpoint 记录实际依赖和理由。

| 当前区域 | 强参考目标 | 迁移重点 |
|---|---|---|
| infra/vision | common/vision | OCR、OpenCV、ROI、模板、像素和结构化技术结果 |
| infra/emulator | common/device | 连接、截图、点击、滑动、按键、启动/停止 |
| infra/system 中无业务语义的配置/异常/文件/日志能力 | common/system | 去除对上层包的导入 |
| infra/data/calibration、图片和模板资源 | common/calibration 或 common/data | 保持只读和唯一资源来源 |
| infra/combat/engine/engine.py、actions.py 的通用流程/动作 | application/combat | 只依赖 common；业务决策由 business 传入 |
| infra/combat/recognition.py、recognizer.py 的原始识别部分 | common/vision | 只返回技术识别结果，不解释业务 |
| infra/combat/rules.py、history.py、engine/plan.py、engine/state.py 中的游戏语义 | business/combat | 规则、计划、结果和业务状态不进入 common |
| infra/ui/navigation/service.py | application/ui/navigation | 语义导航、路由、稳定性确认 |
| infra/ui/pages 的页面动作组合 | application/ui | 组合 Navigator 和 common 原语；不持有业务策略 |
| infra/ui/pages/battle_preparation/fleet_change/_planning.py、_rules.py | business/combat/fleet | 舰队规则和计划算法；若拆出纯技术部分再下沉 |
| infra/ui/pages/battle_preparation/fleet_change 的 OCR/点击/滚动 | application/ui + common/vision/common/device | 应用动作和底层原语分层 |
| infra/ui/pages/battle_preparation/repair.py | application/ui action + business repair | 消除 business 反向依赖；shim 只能委托 |
| ui/decisive/* 的识别原语 | common/vision/common/calibration | HSV、ROI、像素、模板等 |
| ui/decisive/* 的章节/路线/推进/退出决策 | business/combat/decisive | 保留业务语义 |
| GameContext | application/runtime、dispatch、business 按字段拆分 | 不整体复制为 common context |

推荐的最终骨架：

~~~text
autowsgr/
├── server/
├── dispatch/
├── business/
│   ├── combat/
│   ├── homeport/
│   └── system/
├── application/
│   ├── __init__.py
│   ├── combat/
│   │   ├── engine.py
│   │   └── actions.py
│   └── ui/
│       ├── navigation/
│       └── pages/
└── common/
    ├── __init__.py
    ├── device/
    ├── vision/
    ├── ui/
    ├── calibration/
    └── system/
~~~

不要求一次创建所有空目录。只有存在真实调用方和明确职责时才新增子包；__init__.py 保持 export-only，不在其中注册全局状态、执行逻辑或复制兼容代码。

## 7. Checkpoint 执行计划

每个 checkpoint 完成后，Agent 必须：

1. 运行本 checkpoint 的检查命令。
2. 检查 git diff --check 和变更文件。
3. 在任务协调 worktree 的 progress.md 写入 SHA/状态/命令/结果/已知风险。
4. 若有行为变化、边界变化或失败，先记录再进入下一 checkpoint。
5. 能独立回滚时提交一个小 commit；不得把多个未验证阶段堆成一个无法定位的提交。

### Checkpoint 0：基线和 dirty diff 保护

动作：

- 确认 backend Git root、当前分支、HEAD SHA。
- 运行 git status --short --branch、git diff --stat、git diff --name-only、git worktree list --porcelain。
- 阅读 backend 根 AGENTS.md 以及适用于测试/目录的更具体 AGENTS.md。
- 记录当前未提交修改和未跟踪文件，标记哪些属于本任务、哪些明确不属于本任务。
- 搜索 infra、business、application、common 的所有定义、导入方、公开入口、测试和资源引用。

验收：

- 有基线 SHA 和 dirty 文件清单。
- 未覆盖、未回退、未整理原有 dirty diff。
- 有初版迁移矩阵和 import graph。

停止条件：

- 无法确认目标 Git root、分支或 dirty diff 归属时停止写代码。
- 发现现有用户修改与本任务必改文件重叠时，先记录冲突和最小协作方案。

### Checkpoint 1：创建两层包边界

动作：

- 新建 autowsgr/application/__init__.py 和 autowsgr/common/__init__.py。
- 如果目录不存在则一并创建；如果已经存在且为空则直接补齐 package 标记，不重复造目录。
- 在 __init__.py 写清层职责；不放执行逻辑、注册表、全局状态或大规模 re-export。
- 新增最小导入回归检查，确认两个包可导入且不会导入 business/dispatch/server。
- 不在此阶段搬迁实现，先让边界可见、可检查。

验收命令参考：

~~~text
python -c "import autowsgr.application, autowsgr.common"
python -m compileall -q autowsgr/application autowsgr/common
~~~

验收：

- 两个目录均为 Python 包。
- common/application 的初始导入无副作用、无循环依赖。
- diff 只包含边界骨架和必要测试/文档。

### Checkpoint 2：迁移 common 超级基础能力

动作：

- 按调用图逐批迁移设备连接、截图、触控、低层等待、OCR 引擎、OpenCV2 原语、ROI、模板/像素匹配和只读校准资源。
- 将旧 infra 入口改为薄 shim 或同步调用方；不复制实现。
- 对每个迁移模块确认其 import graph 不经过 business/application。
- technical result 只返回基础类型、common 自有类型或结构化识别结果，不返回业务规则对象。

验收命令参考：

~~~text
python -m pytest <common 相关 focused tests> -q
python -m compileall -q autowsgr/common
ruff check autowsgr/common <对应测试路径>
~~~

验收：

- common 内没有 autowsgr.application、autowsgr.business、autowsgr.dispatch、autowsgr.server 或旧 infra 业务实现导入。
- 设备/OCR/视觉单测不需要真实设备。
- 原有调用方若仍使用旧路径，只通过一个 canonical 实现运行。

停止条件：

- 发现某模块必须读取业务规则才能工作时，不得硬塞 common；退回按 application/business 拆分。
- 发现 common 需要依赖 GameContext 才能工作时，先拆出技术资源接口，不得把 GameContext 复制进去。

### Checkpoint 3：迁移 application 公共能力和垂直入口

动作：

- 将通用 CombatEngine、action 组合以及语义 UI Navigator 迁入 application。
- 把页面动作、战斗动作、导航动作拆成 application 的公开入口和同域内部子方法。
- application 只依赖 common；入口参数使用 application 自有 DTO/Protocol/基础类型，不导入 business 类型。
- Navigator 只负责从当前语义锚点执行和确认路径，不决定任务优先级、下一任务或业务停止。
- CombatEngine 只编排动作和技术结果，不决定 LOOT_MAX、SHIP_MAX、舰队选择和战果业务含义。

验收命令参考：

~~~text
python -c "import ast, pathlib; root=pathlib.Path('autowsgr/application'); bad=('autowsgr.business','autowsgr.dispatch','autowsgr.server'); print('application files:', len(list(root.rglob('*.py'))))"
python -m pytest <application 相关 focused tests> -q
ruff check autowsgr/application <对应测试路径>
~~~

验收：

- 每个 application 公开能力至少有一个明确入口和直接调用方。
- business 调用入口，入口再调用 application 子方法，子方法只调用 common，形成垂直链。
- 没有 dispatch/server 直接调用 application 业务能力的旁路。
- 不出现 application -> business 的 import。

### Checkpoint 4：business 入口收口和反向依赖修复

动作：

- 将战斗业务、fleet 规则、修理策略、决战策略等放回 business 对应业务域。
- 修复 battle_preparation/repair.py 的 business 反向依赖：由 business 调用 application repair action；旧页面 shim 只做薄委托。
- 逐个修正所有 business -> infra 真实实现的调用，切换到 application/common canonical API。
- 检查 server/dispatch 只调用 business use-case 入口，不把 application 当作业务注册表。

验收：

- 运行全仓库导入搜索，新的生产代码不再从 business/application 依赖旧 infra 真实实现。
- repair.py 不再由页面层反向导入 business 策略。
- 普通战斗、活动、战役、演习、决战和修理的主要调用方都有明确 owner。
- 旧兼容入口仍然只有一份实现。

建议检查：

~~~text
rg -n "from autowsgr\\.(business|application|dispatch|server).*" autowsgr/infra
rg -n "from autowsgr\\.infra|import autowsgr\\.infra" autowsgr/business autowsgr/application
python -m pytest <战斗、fleet、repair、navigation focused tests> -q
~~~

上述搜索结果需要人工按 shim、测试和生产代码分类，不能只看退出码。

### Checkpoint 5：常量、校准和模板单一来源

动作：

- 完成第 5 节的硬编码清单，每个局部常量都有去留和目标。
- 把重复的返回/确认/战果继续点击、OCR ROI、PixelRule、HSV 范围、模板标识按技术语义收口到 common 资源或 common API。
- 继续使用已有坐标资源契约；不要把颜色、容差、流程状态或业务规则塞进纯坐标 YAML。
- 将 TemplateKey、CombatTemplates、Templates.FightResult 的原始资源入口合并为一个 canonical source；业务结果映射只保留在 business。
- 将 LOOT_MAX、SHIP_MAX、战果等级顺序、舰队策略、次数/停止条件明确留在 business，并为误下沉的旧常量改回正确 owner。
- 对每个坐标/ROI/模板迁移补充调用方和分辨率说明；不把“注释里写了 960x540”误判成运行 bug，也不丢弃真正绝对像素扫描区。

验收：

- 同一物理坐标、同一模板、同一业务规则不再存在多个生产真源。
- 所有迁移后的常量仍有直接测试/调用证据。
- 业务规则没有出现在 common。
- 关键战斗识别链路的输入分辨率、ROI、模板和结果映射保持现有行为。

### Checkpoint 6：请求契约、alias 和状态所有权

动作：

- 在 HTTP/API 边界把 fight_condition 统一转换为明确枚举或受验证的 contract；禁止裸 int 穿过边界后由下游猜测。
- 对未知、空值、越界和类型错误做显式 fail-closed 处理，并为合法/非法输入补测试。
- 将舰名 alias 处理改为任务/请求作用域的不可变输入或明确 owner 的配置快照；禁止模块级全局可写状态污染后续任务。
- 遇到 None、空字符串或非法 alias 时显式拒绝、报告或按已定义规则处理，禁止静默丢弃。
- 按第 4.5 节拆分 GameContext；至少确认设备资源、导航状态、业务状态、每日计数器和停止信号各自唯一 owner。

验收：

- HTTP -> business -> application 的参数类型在每个边界都明确。
- alias 连续执行两个互不相关任务时不会互相污染。
- invalid input 有确定错误和测试证据，不会偷偷采用错误默认值。
- 没有新增第二个全局 context、停止事件或运行时资源 owner。

### Checkpoint 7：全链路静态验证、文档和交付

动作：

- 运行 focused tests，再运行完整 pytest。
- 运行 compile/import 检查、Ruff、pre-commit（按仓库实际可用配置）和 git diff --check。
- 对 application/common 的 import graph 做可重复检查；建议把分层边界检查保留为最小架构回归测试，避免未来再次反向依赖。
- 更新迁移矩阵、常量清单、任务 progress 和必要的架构说明。
- 检查删除的旧文件、shim、资源和测试没有留下重复实现或悬空导入。
- 记录最终 SHA、测试输出摘要、未解决风险和延期项。

验收命令参考：

~~~text
python -m compileall -q autowsgr
python -m pytest -q
ruff check autowsgr testing
pre-commit run --all-files
git diff --check
~~~

本 checkpoint 不运行真实设备 E2E；已有 5/5 实机预算和日志证据按第 0 节约束处理。

最终通过条件：

- autowsgr/application 和 autowsgr/common 存在且可导入。
- 新代码满足 server -> dispatch -> business -> application -> common。
- application 没有上层依赖，common 没有上层项目依赖。
- 战斗 engine/action、语义 Navigator、低层视觉/设备能力和业务规则各有唯一 owner。
- 本节所有审查发现都有关闭证据或明确延期记录。
- full static gates 通过，且没有覆盖其他 Agent dirty diff。

## 8. 不允许的“看似完成”

- 只新增两个空包，却继续让业务从 infra/combat 运行，不能算完成。
- 只把 import 路径改名，不拆分战斗规则、页面适配和识别原语，不能算完成。
- 把所有常量放进 common/constants，尤其是 LOOT_MAX、SHIP_MAX、战果等级和舰队规则，不能算完成。
- 让 common 导入 GameContext、业务枚举或 application service，不能算完成。
- 让 application 直接 import business，不能算完成。
- 在 repair shim、Navigator 或 alias 模块里复制第二份实现，不能算完成。
- 只通过一次 import 或一次手工运行，不能替代分层测试、边界测试和全套静态检查。
- 为本任务追加真实设备操作，不能以 E2E 数量掩盖静态边界未关闭。

## 9. Agent checkpoint 记录模板

每个 checkpoint 在 progress.md 至少写入：

~~~text
Checkpoint: CP<n>
Status: passed | blocked | deferred
Base SHA:
Changed files:
Commands:
Evidence:
Import-boundary result:
Tests:
Dirty files preserved:
Known risks:
Next step:
~~~

发生失败时还要写清：

- 失败的实际命令和完整错误摘要。
- 失败属于代码、环境、旧基线还是用户已有修改。
- 下一次尝试改变了什么假设；不得重复同一失败动作。
- 是否触发停止条件、是否需要用户确认。

## 10. 交付说明

本任务书是强参考执行方案，但不是允许绕过依赖规则的可选建议。Agent 可以基于真实调用图调整具体文件落点，但每一次偏离都必须在 checkpoint 中说明原因、影响和新的验收证据。

完成后不要自动 merge、push、删除 worktree 或清理其他 Agent 的分支。只提交本任务实际改动，并将 backend commit SHA、测试结果和未决风险写入任务协调记录。
