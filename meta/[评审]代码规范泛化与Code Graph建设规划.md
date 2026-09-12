# 代码规范泛化评审与 Code Graph 建设规划

评审状态：`待维护者确认`

评审对象：

- `meta/[规范]navigation-code-style.md`
- `meta/[规范]ui-controller-code-style.md`

本文件只提出问题和修改建议，不直接修改上述规范。规范调整须经维护者确认后另行执行。

## 一、总体结论

两份规范已经覆盖文件说明、配置归属、函数命名、私有对象和基础验证，但目前更像一次
UI Controller 治理任务形成的经验合集，还不能直接作为全项目长期唯一标准。

主要原因：

1. 基础规范的文件名与实际适用范围不一致。
2. 通用规则在两份文档重复，后续必然产生漂移。
3. 若干规则与仓库现实、Ruff 配置或 Battle Page 样板冲突。
4. 缺少公共 API、包边界、层级方向、状态所有权和错误契约。
5. 大部分要求只能人工判断，没有机器可执行门禁。
6. 缺少为 Code Graph 提供稳定语义和动态边声明的约定。

建议先重组规范体系，再推广到整个项目和 Agent 全局约束。

## 二、问题清单

| 级别 | 当前问题 | 影响 | 建议 |
|---|---|---|---|
| 高 | `navigation-code-style.md` 实际是全项目 Python 文件规范 | 名称误导，UI 规范反向继承导航规范 | 重命名为通用 Python 规范；另建真正的导航专项规范 |
| 高 | `navigation-code-style.md` 未进入当前 Meta Git 白名单 | 新 worktree 和其他 Agent 无法稳定取得基础规范 | 将规范加入跟踪白名单，并把“规范文件存在且受版本控制”设为门禁 |
| 高 | 两份规范重复文件说明、import、配置、顺序、docstring 和验证规则 | 修改一处后另一处容易过期 | 通用规则只保留一份，专项规范只写增量 |
| 高 | UI 规范默认把组合业务动作放在原子动作之后 | 与用户确认的 Battle Page“主流程在前、实现方法在后”冲突 | 改为 `__init__ → 主流程 → 支撑方法 → 私有辅助` |
| 高 | 缺少“外部只能导入包入口”的明确规则 | 深层导入和私有 API 兼容不断扩散 | 定义包级公开入口、`__all__` 和 deep-import 门禁 |
| 高 | 缺少状态所有权、输入/结果和异常约束 | 出现 `last_changed_fleet`、双向代理和含义不清的 bool | 要求单一状态所有者、结构化结果和明确异常 |
| 高 | 缺少项目层级允许依赖表 | “上层/下层”只能靠经验判断 | 增加机器可读层级与允许边配置 |
| 中 | `as` 规则过宽，仓内现有约 127 处导入别名 | 会误伤 `numpy as np` 等事实标准，难以落地 | 只禁止兼容/隐藏语义别名；维护允许别名表和例外理由 |
| 中 | 坐标一律要求 `0.xxxx`，但已有校准需要更高精度 | 四舍五入可能改变映射像素和 OCR ROI | 四位作为默认展示；以支持分辨率像素等价为硬门禁，必要时允许更高精度 |
| 中 | 页面模板检查规定放 `page.py`，其他像素/ROI 识别放 `recognition.py` | 同一“截图 → 页面事实”职责被拆散 | recognition 拥有纯视觉实现；page 可提供稳定薄入口 |
| 中 | 页面目录模板不能覆盖 `formation` 等跨页面业务流程 | 全项目推广会把非页面流程伪装成 Page | 增加“页面包”和“业务流程包”两种模板 |
| 中 | 文件级 `上层调用/下层依赖` 完全手工维护 | 很容易与真实 import/call 图漂移 | Code Graph 生成事实，docstring 只保留关键语义并自动校验 |
| 中 | 验证只写 focused pytest/pre-commit，缺少层级 | Agent 无法判断重构中间阶段何时可继续 | 定义结构、行为、集成、发布四级门禁 |
| 中 | 没有动态导入、注册表、回调和资源边声明规则 | 静态图无法覆盖导航注册、FastAPI 路由和模板资源 | 增加声明式动态边或图谱插件约定 |
| 低 | 每个常量都要求独立注释 | 同质数组/映射会产生重复噪声 | 校准项逐项注释；同质数据允许组级契约 + 异常项注释 |
| 低 | 所有业务内部函数都要求完整 Args/Returns | 简短私有函数文档可能比实现更长 | 公共入口强制；复杂私有函数强制；简单私有函数允许单行 docstring |
| 高 | UI 规范含“diff 不包含 bath_page 非 A1 修改” | 一次性任务规则污染长期规范 | 移回对应任务书，长期规范禁止项目任务特例 |

## 三、建议的规范层级

建议从当前两份文档重组为以下四层：

```text
[规范]python-code-style.md
    ├── 文件说明、import、配置、注释、docstring、函数顺序、基础验证
    │
    ├── [规范]module-boundary-code-style.md
    │       包入口、公开/私有 API、层级方向、状态与结果、Code Graph 元数据
    │
    ├── [规范]ui-controller-code-style.md
    │       页面包、流程包、page/recognition/constants、页面动作前缀
    │
    └── [规范]navigation-code-style.md
            NavEdge、页面来源、终态验证、导航栈、模式专用返回和禁止通用假边
```

规则所有权：

- 通用规范只描述所有 Python 文件都适用的规则。
- 模块边界规范描述包和项目层级，不重复格式规则。
- UI 规范只描述页面和 UI 业务流程的特有边界。
- 导航规范只描述跨页面路径、来源、终态和导航图。
- 任务特例、保护目录、允许破坏范围和具体测试命令只写任务书。

## 四、需要补齐的核心规则

### 4.1 页面包与流程包

页面包默认：

```text
xx_page/
├── __init__.py
├── page.py
├── recognition.py   # 有真实视觉逻辑时
└── constants.py     # 有真实配置时
```

业务流程包默认：

```text
xx_flow/
├── __init__.py
├── workflow.py
├── operations.py    # 有设备/外部动作时
├── recognition.py   # 有视觉输入时
├── constants.py     # 有配置时
└── models.py        # 有独立输入/结果时
```

建立目录的条件：一个功能必须拥有明确业务动词、独立输入、可观察结果，并能被父流程作为
单一步骤调用。纯解析、规划或排序阶段默认只是所属流程内的文件，不单独建空目录。

页面自身的主业务流程仍放在页面包的 `page.py`，不能因为它包含流程就再增加一层
`workflow.py`。只有跨页面流程或不属于单一页面的业务子流程才使用流程包；流程包中的
真实节点满足上述独立输入、结果和所有权条件时，可以继续拆成子目录。

Fleet 作为首个样例域采用三类一级边界：`main_page` 页面控制器、`formation` 选船核心和
`support` 辅助功能。`formation` 内的编队识别、编队调整和编队选船是三个有独立事实或
结果的流程节点，因此允许分别建包；规则匹配、候选规划和排序算法仍是编队调整包内文件，
不得继续机械升级为目录。

### 4.2 文件和类内顺序

统一为：

```text
文件级说明
→ import
→ TYPE_CHECKING
→ logger
→ 文件配置
→ 数据模型/类型
→ 对外主流程
→ 主流程直接调用的实现方法
→ 跨流程私有辅助
```

类内顺序：

```text
__init__
→ 主业务流程
→ 状态检查/读取
→ open/select/click/confirm 等支撑动作
→ go_back/navigate_to
→ 私有辅助
```

业务调用链优先于按前缀机械分组。

### 4.3 Public API

- 每个包必须有一个明确的公开入口文件，通常为 `__init__.py`。
- `__all__` 是公开符号事实来源；不在 `__all__` 中的符号视为包内部实现。
- 包外生产代码只能导入包公开入口，不得导入实现文件。
- 同一业务能力只能有一个公开所有者。
- 不使用 `__getattr__`、`sys.modules` 替换、动态属性挂载或导入别名伪造兼容 API。
- 兼容策略由任务或发布契约决定；长期规范不得默认要求保留兼容。

### 4.4 输入、结果、错误和状态

- 外部字典、YAML、请求体先在边界转换为规范化模型。
- 多字段结果使用不可变结果类型，不通过对象旁路属性让调用方二次读取。
- `bool` 只用于无歧义的二元判断；需要失败原因时使用结果类型或明确异常。
- 可写状态必须声明唯一所有者、创建点、更新点和销毁点。
- callback 只用于真实反向通知，不用于把同模块方法重新注入自身流程。
- 页面动作必须说明成功终态；无法确认时 fail visibly。

### 4.5 Import 别名

建议规则：

- 禁止用别名维持旧包名、隐藏跨层依赖或把私有实现伪装成公共 API。
- 允许项目批准的事实标准别名，例如 `numpy as np`。
- 同名冲突需要别名时，优先导入模块并通过模块名访问；仍需别名时写明原因。
- 允许别名清单进入机器配置，未知别名由 Code Graph/lint 报告。

### 4.6 坐标精度

- 坐标必须使用 `[0, 1]` 的归一化值并聚合同一语义轴。
- 四位小数是默认可读格式，不是牺牲校准精度的绝对上限。
- 更高精度必须能够说明来源分辨率或校准依据。
- 变更坐标后必须验证所有支持分辨率上的目标像素等价或明确偏移。

## 五、Code Graph 建设目标

Code Graph 用来回答：

- 一个模块由谁导入、它依赖谁？
- 一个公开入口最终调用哪些实现和 common 能力？
- 一个函数、配置、模板或页面状态由谁消费？
- 哪些调用穿透了包边界或违反层级方向？
- 哪些定义没有调用方，哪些公开 API 没有真实消费者？
- 哪些测试覆盖了指定流程和关键边？
- 重构前后哪些边新增、删除或改变所有者？

“完整”定义为：静态可确定关系全部收集，动态关系通过声明或插件补齐；不得把 Python
动态调用猜测成确定事实。

## 六、图谱模型

### 6.1 节点

| 节点类型 | 示例字段 |
|---|---|
| repository/module/package | 路径、层级、业务域、是否公开 |
| class/function/method | qualified name、文件、行号、签名、可见性 |
| model/state | 所有者、可变性、创建/更新位置 |
| config/resource | YAML key、模板、坐标组、数据文件 |
| registry/route/page | PageName、NavEdge、HTTP 路由、任务类型 |
| test | 测试节点和被验证目标 |

稳定节点 ID 使用：`repository:path::qualified_name`。

### 6.2 边

| 边类型 | 含义 |
|---|---|
| `imports` | 模块导入 |
| `exports` | 包公开导出 |
| `calls` | 可静态解析函数/方法调用 |
| `constructs` | 创建类或状态对象 |
| `reads` / `writes` | 读取或更新状态 |
| `registers` | 页面、导航、路由、任务注册 |
| `loads_config` | 读取配置键或 YAML |
| `uses_resource` | 使用模板、图片、坐标和数据文件 |
| `tests` | 测试覆盖目标 |
| `declared_dynamic` | 人工声明的动态导入、回调或反射关系 |

每条边保存来源文件、行号、解析方式和置信度。

## 七、实现建议

第一版不新增依赖。使用 Python 标准库：

- `ast`：定义、导入、调用、装饰器和字符串资源引用；
- `pathlib`：仓库和路径处理；
- `json`：稳定图谱产物；
- `tomllib`：读取层级和例外配置；
- `collections`：邻接表、循环和可达性检查。

`uv.lock` 中虽然存在 `networkx`，但它不是本项目直接依赖，第一版不得依赖传递依赖。

建议新增：

```text
tools/code_graph.py
testing/tools/test_code_graph.py
docs/architecture/code-graph.md
```

配置优先写入 `pyproject.toml`：

```toml
[tool.autowsgr-code-graph]
roots = ["autowsgr", "testing", "tools", "examples"]
exclude = [".git", ".venv", "build", "dist", "__pycache__"]

[[tool.autowsgr-code-graph.layers]]
name = "common"
path = "autowsgr/common"
allows = []
```

完整层级表必须依据实际架构单独确认，不能直接使用目录名猜测允许方向。

## 八、CLI 与产物

建议最小 CLI：

```powershell
uv run python tools/code_graph.py build --output .artifacts/code-graph/graph.json
uv run python tools/code_graph.py check
uv run python tools/code_graph.py explain autowsgr.application.ui.controller.fleet
uv run python tools/code_graph.py diff old.json new.json
```

产物：

```text
.artifacts/code-graph/
├── graph.json
├── violations.json
├── modules.mmd
└── summary.md
```

- `graph.json` 是机器事实来源。
- `violations.json` 用于 CI 和 Agent 门禁。
- `modules.mmd` 只生成选定业务域的 Mermaid 概览，避免全仓大图不可读。
- `summary.md` 提供入口、主要路径、循环、孤儿定义和高风险动态边摘要。
- 大型生成图默认不提交 Git；提交工具、配置、文档和必要的小型架构摘要。

## 九、动态关系补齐

第一批插件只覆盖真实现有机制：

1. `__all__` 和包级重导出。
2. `register_page` 与 `PageName`。
3. `NavEdge` 和导航图注册。
4. FastAPI 路由装饰器。
5. 配置读取和常见 YAML key。
6. `Templates.*`、资源路径和数据加载器。
7. pytest import、patch 目标和测试文件到目标符号的关系。

无法静态解析的调用记录为 unresolved，不通过函数名猜测自动连边。确需补齐时使用独立
声明文件或受控注释，并要求文件/行号和原因。

## 十、Code Graph 实施阶段

### CG0：事实与层级契约

- 确认仓库、层级、业务域、公开入口、排除目录和允许依赖边。
- 固定 JSON schema、节点 ID、边类型和置信度。
- 先以 Fleet 作为样例域，固定 `main_page -> formation/support`、
  `formation.workflow -> fleet_recognition/fleet_adjustment` 和
  `fleet_adjustment -> ship_selection` 的允许方向。

### CG1：模块、定义和导入图

- 收集 package/module/class/function/method。
- 收集 import、TYPE_CHECKING import、`__all__` 和重导出。
- 检查 deep import、私有导入、孤儿模块和模块循环。

### CG2：调用与状态图

- 收集可静态解析的 call/construct/read/write。
- 标记动态 dispatch、callback、反射和无法解析边。
- 对 Fleet 重构前后图执行差异检查。

### CG3：注册、配置、资源和测试图

- 加入导航、页面、FastAPI、配置、模板、YAML 和测试边。
- 生成维护者可读的业务域摘要。

### CG4：机器门禁

- 接入 scoped pre-commit 或 CI，只检查受影响业务域。
- 首批硬门禁：不存在节点、禁止层级边、包外私有导入、未声明公开出口。
- 循环、孤儿定义、未覆盖流程先作为报告，稳定后再升级为硬门禁。

### CG5：Agent 与维护者接入

- Agent 开始任务前执行 `explain <module>`，获得入口、上层、下层、状态和测试。
- Agent 修改后执行 `check` 和 `diff`，把图谱差异写入交付报告。
- 架构文档引用图谱摘要，不手写完整依赖清单。
- IDE 集成和交互式网页只有在 CLI/JSON 稳定后再建设。

## 十一、验收标准

- 同一通用规则只在一份规范拥有权威定义。
- 专项规范不包含一次性任务名、保护目录或历史阶段编号。
- 规范中的硬门禁都有对应命令或明确人工检查方法。
- Code Graph 对 Fleet 的模块、定义、导入和公开出口覆盖率为 100%。
- 所有静态边保留可点击文件和行号证据。
- 动态边明确区分已声明、未解析和推测，推测边不参与硬门禁。
- 不依赖未声明的第三方包，不扫描 `.git`、虚拟环境、构建物或缓存。
- 相同源码生成字节稳定或语义稳定的 JSON，便于 diff。

## 十二、需要维护者确认的决定

1. 是否将当前 `navigation-code-style.md` 重命名为通用 Python 规范，并新建真正的导航规范。
2. 是否允许 `numpy as np` 等批准别名，还是坚持全仓彻底禁用 `as`。
3. 坐标规则采用“默认四位 + 像素等价”还是“绝对四位”。
4. 页面模板/像素检查的实现是否统一归 `recognition.py`，由 `page.py` 暴露薄入口。
5. 是否接受根包 `__all__` 作为公共 API 的机器事实来源。
6. Code Graph 生成的大型 JSON/Mermaid 是否只作为 CI artifact，不提交仓库。
