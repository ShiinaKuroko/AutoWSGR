# Code Graph

## 目的

Code Graph 是 AutoWSGR 的架构治理工具，不是运行时业务模块。它用于回答：

- 模块、包、公开符号和测试之间的依赖关系是什么；
- 一个入口会调用哪些本地实现和资源；
- 哪些导入违反层级方向；
- 哪些注册、路由、配置和资源关系无法从静态代码确定；
- 架构重构前后哪些节点和边发生了变化。

当前仓库的运行时导航图位于
autowsgr/application/ui/navigation/graph/，它描述游戏页面路径，与本工具无关。

## 文件归属

| 内容 | 位置 |
| --- | --- |
| 生成、检查、解释和对比 CLI | tools/code_graph/code_graph.py |
| 工具测试 | testing/tools/test_code_graph.py |
| 根、排除目录和层级规则 | pyproject.toml 的 tool.autowsgr-code-graph |
| 生成结果 | .tmp/code-graph/，默认不提交 |
| Agent 使用规则 | 项目根 AGENTS.md，由后续阶段另行加入 |

第一版只使用 Python 标准库 ast、pathlib、json、tomllib 和 collections，
不依赖传递安装的 networkx。

## 使用方式

从仓库根目录执行：

~~~powershell
uv run python tools/code_graph/code_graph.py build
uv run python tools/code_graph/code_graph.py check
uv run python tools/code_graph/code_graph.py explain autowsgr.dispatch
uv run python tools/code_graph/code_graph.py diff old.json new.json
~~~

build 默认读取 pyproject.toml，扫描 autowsgr、testing、tools 和 examples，
写入 .tmp/code-graph/graph.json。基线生成应增加 --require-clean，拒绝把未提交
修改误当成可复现现状：

~~~powershell
uv run python tools/code_graph/code_graph.py build --require-clean
~~~

可以用 --root 指定其他仓库根目录，用 --output 指定快照路径。
check 只校验已有快照，不会隐式重建图。

## 图谱事实

节点包含：

- package/module；
- class/function/method；
- route、registry；
- 配置、YAML、模板和其他静态资源。

节点 ID 使用 repository:relative-path::qualified_name。节点和边按稳定顺序
写入 JSON，便于审查和比较。快照还记录源代码 revision、dirty 状态和 dirty
文件列表。

边包含：

| 类型 | 来源 |
| --- | --- |
| imports | import 和 from ... import ... |
| exports | __all__ |
| calls / constructs | 可静态解析的函数调用和类构造 |
| registers | FastAPI 路由、页面/任务注册和 NavEdge 调用 |
| loads_config | 常见 YAML/config 加载调用 |
| uses_resource | 代码中的 YAML、图片、模型等资源字符串 |
| tests | testing/ 模块对本地目标的导入 |
| declared_dynamic | importlib.import_module 或配置中的声明关系 |

无法可靠解析的动态关系写入 unresolved，不得根据函数名猜测调用边。
当前第一版重点覆盖静态模块/符号/导入关系和少量现有动态机制；状态
reads/writes、复杂反射和运行时 callback 仍需后续声明或插件支持。

## 层级检查

当前配置表达五层方向：

~~~text
server -> dispatch -> business -> application -> common
~~~

check 会校验快照中 imports 边的配置层级。测试、工具和 examples
暂不套用生产层级规则。层级违规先作为明确检查结果，不通过增加注释或
兼容导出掩盖。

动态关系需要补充时，使用结构化配置，并保留原因：

~~~toml
[[tool.autowsgr-code-graph.dynamic_edges]]
source = "autowsgr:autowsgr/dispatch/registry.py::build_executor"
target = "autowsgr:autowsgr/business/combat/exercise/executor.py::ExerciseExecutor"
type = "declared_dynamic"
reason = "task_type registry resolves the executor lazily"
path = "autowsgr/dispatch/registry.py"
line = 53
~~~

## 注释和 docstring

注释与图谱有关，但不是同一种事实：

- AST 和结构化配置是 import、call、register 和 resource 边的事实来源；
- 公共模块、类和函数的 docstring 应说明职责、输入、输出、状态所有权、
  副作用和失败边界；
- 不在 docstring 中手工维护完整的 caller/dependency 列表；
- 动态关系优先使用结构化声明；受控注释只能作为有明确格式、来源、目标和
  原因的窄范围补充；
- 图谱与注释冲突时，先报告事实图与语义说明的差异，不静默让注释覆盖 AST。

因此，不需要为每个普通函数增加 Code Graph 注释；只在公共边界和确实
无法静态解析的关系上补充语义。

## 三阶段流程

### 第一阶段：现状基线

1. 选择一个干净、固定的 commit，执行 build --require-clean。
2. 审查节点、导入边、层级规则、公开出口和 unresolved 动态关系。
3. 保存 JSON 快照路径、源代码 SHA、扫描范围和已知限制。
4. 大型 JSON/Mermaid 只作为本地或 CI artifact，不提交仓库。

当前共享 worktree 有其他未提交重构改动，不能直接作为可复现基线；应等
相关改动形成干净提交后再生成正式基线。

### 第二阶段：coding 期间按需维护

Agent 默认不会自动发现或维护 Code Graph。用户明确要求维护时，才执行：

1. 针对受影响模块执行 explain；
2. 重新 build、check；
3. 与任务基线执行 diff；
4. 在交付记录中说明新增、删除、改变和未解析的边。

是否把这组触发条件加入项目根 AGENTS.md，属于下一阶段的独立变更。

### 第三阶段：架构升级后复核

在升级后的干净 commit 生成新快照，与第一阶段基线比较：

- 模块和公开符号是否按预期迁移；
- 依赖边是否符合五层方向；
- 状态和资源所有权是否出现重复；
- 动态边是否从 unresolved 变为有证据的声明；
- 删除的旧路径是否留下悬空导入或测试关系。

差异结果用于架构验收，不自动判定所有新增边都是错误。

## 限制

- Python 动态反射、运行时拼接导入名、复杂 callback 和框架内部注册无法
  仅靠 AST 完整还原；
- calls 只收集可静态解析的本地符号，第三方调用不会伪造本地图节点；
- 当前图谱不执行代码，不替代 pytest、import smoke 或运行时 E2E；
- graph JSON 的 source revision 和 dirty 文件列表必须与审查记录一起看，不能
  把过期快照当成当前代码事实。
