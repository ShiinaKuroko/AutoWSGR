Task ID: `20260830-autowsgr-upgrade`
Task Status: `done`
Next Step: 无；Fleet 业务流程重构已完成，后续按综合报告进入业务联调。

## Goal

已完成 UI Controller 的 backyard、sidebar、home 和 sortie 页面域治理；保留这些历史成果
和现有未提交修改，不在当前 Fleet 任务中返工。

当前追加目标：将 `application/ui/controller/fleet/` 重写为页面控制器、选船核心和辅助功能
三个一级业务边界；页面控制器负责 UI 与主流程编排，选船核心按编队识别、编队调整和
编队选船三个流程节点组织，补给、战役支援、维修等状态能力归入辅助功能。

## Scope

- `backyard/main_page/`：后院主页面导航控制器。
- `backyard/bath_page/`：浴室页面控制器及 OCR 规则。
- `backyard/canteen_page/`：食堂页面控制器。
- 更新所有生产、导航和测试导入方。
- `sidebar/` 下管理侧边栏主入口、好友、强化和建造/拆解页面。
- 按两份代码规范重塑整个 `sidebar` 页面域的常量、命名、注释和函数顺序。
- 不修改 BathPage 业务逻辑；不创建空的 recognition.py。
- Fleet 现有业务规则作为迁移事实保留，但允许彻底重写其目录、继承、状态和调用结构；
  不为旧 `fleet_change` API 或测试维持兼容。

### Phase 30: Fleet Main Page Capability Split

- [x] 建立 `preparation`、`fleet_status`、`supply`、`repair` 能力包及统一出口。
- [x] 将 `BattlePreparationPage` 改为无继承页面类，只编排流程并调用能力入口。
- [x] 保留换船算法行为，通过 `fleet_change` 私有适配对象承接页面依赖。
- [x] 删除旧的 flat Mixin/动作文件，更新生产、测试和工具引用。
- [x] 运行换船/准备页及相邻业务回归、导入/编译检查和 `git diff --check`。
- **Status:** complete

### Phase 30 Errors

| Error | Attempt | Resolution |
|---|---:|---|
| 首轮专项测试暴露页面缺少旧私有辅助出口，且测试仍 patch 已迁移的检测路径 | 1 | 通过页面兼容出口和新 `fleet_status.recognition` patch 路径恢复测试契约。 |
| Ruff 拒绝能力包中的 lambda 赋值 | 1 | 改为命名默认回调函数，目标 pre-commit 随后全部通过。 |

### Phase 31: Fleet Rewrite Taskbook and Standards Audit

- [x] 参考 Battle Page 样板编写 Fleet 主流程/子流程重构任务书。
- [x] 明确删除全部旧兼容、允许阶段性功能失效和不可放宽安全边界。
- [x] 评审两份现有规范的重复、冲突、不可执行和泛化缺口。
- [x] 规划标准库实现的全项目 Code Graph、机器门禁和 Agent 接入方式。
- [x] 按维护者确认的三类一级边界重写任务书目录、依赖、方法归属和实施阶段。
- [x] 对账现有 Fleet 全部定义，确保每个定义只有一个目标业务归属。
- [ ] 维护者确认规范重组、导入别名、坐标精度、视觉归属、`__all__` 和图谱产物策略。
- **Status:** in progress

### Phase 31 Errors

| Error | Attempt | Resolution |
|---|---:|---|
| 两份新 Markdown 首轮 pre-commit 缺少文件末尾换行 | 1 | 接受 end-of-file-fixer 修正，重跑全部通过。 |
| 合并更新 findings/progress 时使用了跨文件错误上下文 | 1 | 读取实际尾部后拆成精确补丁，未覆盖既有记录。 |
| 并行执行的 Python AST 一行命令因 JavaScript/PowerShell 嵌套引号解析失败 | 1 | 命令未启动且未改文件；停止复用该写法，改用分文件读取和简单 `rg` 清单。 |
| 任务书整文件补丁同时删除并新增同一路径，被 `apply_patch` 拒绝 | 1 | 旧文件未变化；改为两个连续的直接补丁操作完成替换。 |
| F0 定义归属补充补丁因 `findings.md` 尾部上下文已变化而被拒绝 | 1 | 文件未变化；读取实际尾部后改用单独追加补丁。 |
| 页面基础实现结论补充补丁因 `findings.md` 上下文已变化被拒绝 | 1 | 文件未变化；改为读取尾部后追加记录。 |
| 标记 F0 的复合补丁因 `task_plan.md` 和 `progress.md` 上下文已变化被拒绝两次 | 2 | 未产生部分修改；改为逐文件读取并分别应用任务书、计划和进度补丁。 |
| F1 页面补丁的长模板字符串包含未转义反引号，先执行的删除步骤成功而新增步骤未执行 | 1 | 已确认 `page.py` 缺失；记录后用不含模板反引号的直接新增补丁恢复目标文件。 |
| F0 状态复合补丁报告上下文失败，但前置任务书和计划文件已部分生效 | 1 | 重新读取三文件确认实际状态；补齐任务书 F0、计划和进度，不覆盖其他修改。 |
| F1 多行 PowerShell 验证命令因 JavaScript 字符串转义未启动 | 1 | 改用 `String.raw` 命令重新执行，compileall、入口导入和 smoke 通过。 |
| F2 目标 pre-commit 首次由 Ruff 自动修正 5 处导入/格式问题并返回失败 | 1 | 接受机械修正，重跑同一组目标文件后全部通过。 |
| F2 识别 smoke 使用 `Lv. 120` 作为等级样例导致断言失败 | 1 | 读取项目实际 `parse_fleet_level` 规则后更换验证样例，未修改识别实现。 |
| F4 目标 pre-commit 发现调整参数与页面坐标都命名为 `constants` | 1 | 直接导入页面公开 `CLICK_SHIP_SLOT`，保留调整参数模块名，重跑后通过。 |
| F4 调整对象 smoke 把无约束规则误断言为需要约束校验 | 1 | 使用带等级约束的规则重跑；未修改业务实现。 |
| F5 总入口补丁同时删除并新增同一路径 `formation/__init__.py` 被工具拒绝 | 1 | 未产生部分修改；确认状态后拆成新增 workflow、更新 init 和更新 page 的独立补丁。 |
| F5 总入口补丁使用错误的长模板字符串，未可靠落地 | 1 | 确认状态后拆成新增 workflow、更新 init 和更新 page 的独立补丁。 |
| F6 补给 smoke 将两个 `with` 语句写在一行导致 Python 语法错误 | 1 | 改用标准输入执行短脚本，自动补给开关两条路径通过。 |
| F7 三态支援 smoke 复用一次性像素距离替身导致 StopIteration | 1 | 每次识别创建独立替身，三态和 fail-closed 测试通过。 |
| F8 维修新增补丁误写为共享主仓路径，旧文件删除阶段找不到目标 | 1 | 确认无部分新增后改用绑定 worktree 正确路径补齐维修包。 |
| F8 目标 pre-commit 暴露 F2 识别文件类型导入缩进错误 | 1 | 修正 `OCREngine` 导入缩进，重跑 AST/Ruff 通过。 |
| F9 生产批次 pre-commit 自动修正 9 处导入和 1 个格式文件 | 1 | 接受机械修正，重跑生产批次后通过。 |
| F9 导航 registry smoke 假设错误页面序列化键导致断言失败 | 1 | 改用 `PageName.value` 验证，registry smoke 通过。 |
| F9 新船池测试沿用当前 OCR 不支持的自定义别名样例 | 1 | 读取实际匹配结果，改用当前稳定名称样例，focused 测试通过。 |
| F9 演习测试替身缺少新 `adjust_fleet`/`read_ship_damage` 方法 | 1 | 同步替身接口，演习专项恢复通过。 |
| F9 普通战斗测试仍覆盖已删除页面内部快照测试 | 1 | 删除旧内部实现测试，保留普通业务配置和路由测试。 |
| F9 战役测试替身未接收 `recognize_ship_types` 关键字 | 1 | 补齐替身参数，战役专项恢复为 31 passed。 |

## Phases

### Phase 1: Discovery

- [x] 确认绑定 worktree、现有未提交改动和目标目录状态。
- [x] 盘点三个页面包及直接导入方。
- **Status:** complete

### Phase 2: Move Packages

- [x] 创建 `backyard` 领域包。
- [x] 移动 `backyard_page` 到 `backyard/main_page`。
- [x] 移动 `bath_page` 和 `canteen_page` 到 `backyard/` 下的同级目录。
- **Status:** complete

### Phase 3: Update References

- [x] 更新生产、导航、测试和文档中的导入路径。
- [x] 更新文件级依赖说明。
- [x] 保留已有页面公共入口和行为语义。
- **Status:** complete

### Phase 4: Verify

- [x] 检查旧路径无残留。
- [x] AST/编译检查；运行时导入 smoke 已执行但受环境缺少 `pydantic` 阻塞。
- [x] 执行 `git diff --check` 并核对变更范围。
- **Status:** complete

### Phase 5: Sidebar Controller Reorganization

- [x] 创建 `controller/sidebar/` 领域包。
- [x] 将侧边栏主控制器、好友、强化和建造页面组织为同级页面包。
- [x] 更新生产、导航、业务、测试和文档中的导入路径。
- [x] 保留已有页面行为、延迟导入和当前未提交修改。
- [x] 完成结构、AST/编译、旧路径和差异检查；运行时导入受环境缺少 `yaml` 阻塞。
- **Status:** complete

### Phase 6: Sidebar Style and Ownership Rewrite

- [x] 将 sidebar、friend、intensify 的页面专属校准移入各自 `constants.py`。
- [x] 统一页面检查、读取和关闭动作的函数前缀及顺序。
- [x] 按导航规范重写四个页面包的文件级说明、功能分区和业务 docstring。
- [x] 删除确认无消费者的公共校准包装和 YAML，并更新全部调用方。
- [x] 完成 focused 静态、编译、导入和差异验证；运行时导入受环境缺少 `pydantic` 阻塞。
- **Status:** complete

### Phase 7: Legacy Rule Compatibility Patch

- [x] 在 `_parse_legacy_condition()` 中规范化大小写和组合运算符空格。
- [x] 保持单等号非法、双等号合法的现有语义。
- [x] 增加解析器参数化测试和 `NodeDecisionRequest` API 边界测试。
- [x] 仅运行目标 pytest 和 `git diff --check`，不 cherry-pick 或 merge `c5a464c`。
- **Status:** complete

### Phase 8: Remaining UI Controller Boundary Audit

- [x] 明确 `mission_page`、`event`、`decisive`、`map`、`battle_preparation` 的页面域边界。
- [x] 确认地图面板、决战页面和出征准备之间的物理归属与调用关系。
- [x] 按风险分批制定页面包、常量、OCR 和注释重塑顺序。
- [x] 不在边界确认前移动剩余 Controller 文件。
- **Status:** complete

### Phase 9: Home Page Controller Rewrite

- [x] 将 `controller/home/main_page` 重命名为 `controller/home/main_page_page`，并将 `controller.py` 规范为 `page.py`。
- [x] 将 `MainPage` 统一命名为 `HomePage`，同步所有生产、导航、业务、测试和工具调用方。
- [x] 将主页专属校准从通用加载包装下沉到页面 `constants.py`，保留业务状态名 `PageName.HOME`。
- [x] 按规范整理主页、浮层和活动导航的文件说明、绝对导入及函数分区。
- [x] 验证旧路径/旧类名无遗漏，运行 AST/compile、focused 测试和 `git diff --check`。
- **Status:** complete

### Phase 16: Sortie UI Controller Governance

- [x] 创建并执行 `meta/[任务书]出征模块治理任务.md`。
- [x] 盘点并治理 `battle_preparation`、`decisive`、`event`、`map` 和
  `home/event_nav.py` 的原目录结构、注释、函数命名、函数顺序和导航边界。
- [x] 对 `battle_preparation/fleet_change` 做边界审计；未证明 UI 无关前不下沉到
  `common`，保留用户已验证的选船行为。
- [x] 上下文/OCR问题写入 `[todo]` 台账，其他问题写入出征模块治理报告；不修改
  `bath_page`。
- **Status:** complete

### Phase 17: Operations Controller Aggregation

- [x] 创建 `autowsgr/application/ui/controller/operations/` 业务聚合包。
- [x] 将 `mission_page/` 移动到 `operations/mission_page/`，保留其页面、数据和
  OCR 文件结构。
- [x] 同步所有生产、导航、测试和文档导入方；保持 `MissionPage`、
  `PageName.MISSION` 和导航行为不变。
- [x] 记录四区域目录决策，不移动 `home`、`backyard`、`sidebar` 或其他页面组。
- [x] 完成 import smoke、compileall、旧路径扫描、scoped pre-commit 和
  `git diff --check`。
- **Status:** complete

### Phase 18: PageName Semantic Naming Audit

- [x] 盘点 `PageName` 的全部成员、序列化值、注册表和仓内调用方。
- [x] 区分页面状态、页面内浮层和视觉资源名称，确认 `CHOOSE_REPAIR` 当前没有页面状态调用方。
- [x] 将候选映射和兼容边界写入 `meta/[todo]PageName语义统一.md`，延期后续专题处理。
- [ ] 确认成员名是否按建议映射统一，且序列化值保持不变。
- [ ] 按确认后的映射同步生产代码、测试、工具和文档，并完成 focused 验证。
- **Status:** deferred by user

### Phase 19: Mission Page Module Split

- [x] 将页面标签和页面侧派生变量移入 `mission_page/page.py`。
- [x] 将任务页面坐标、颜色、扫描阈值和滚动参数以静态值移入 `mission_page/constants.py`。
- [x] 将任务结果模型、任务库读取和 OCR 识别代码收敛到 `mission_page/recognition.py`。
- [x] 删除职责混杂的 `mission_page/data.py`，保持包级公共导出和任务页面行为不变。
- [x] 完成相关测试、compileall、import smoke、scoped pre-commit 和 `git diff --check`。
- **Status:** complete

### Phase 20: Sortie Page Aggregation and Partial Governance

- [x] 创建 `application/ui/controller/operations/sortie_page/`，聚合出征、演习、战役、远征和决战五个顶部标签模块。
- [x] 迁移 `sortie.py` 和 `decisive.py` 文件，保持文件内容和行为不变。
- [x] 迁移并治理 `exercise.py`、`campaign.py` 和 `expedition.py`，按两份 UI Controller/导航规范整理说明、分区、命名和函数顺序。
- [x] 同步 `MapPage`、工具、测试和文档的导入路径；不改变地图 Mixin 组合和现有导航契约。
- [x] 完成结构、focused pytest、compileall、import smoke、目标 pre-commit 和 `git diff --check`，并重读出征任务书。
- **Status:** complete

### Phase 21: Sortie Submodule Template Split

- [x] 将 `sortie_page/exercise.py`、`campaign.py` 和 `expedition.py` 分别升级为 `exercise_page/`、`campaign_page/` 和 `expedition_page/`。
- [x] 按 UI Controller 规范拆分三个目录的页面执行、私有常量和必要的 OCR 识别职责。
- [x] 演习和远征没有实际 OCR 时不创建空 `recognition.py`；战役保留次数/获取数量 OCR 行为。
- [x] 保持 `sortie.py`、`decisive.py` 实现不变，只同步 sortie 聚合入口和受影响调用方。
- [x] 完成结构、focused pytest、compileall、import smoke、目标 pre-commit 和 `git diff --check`，并重读出征任务书。
- **Status:** complete

### Phase 22: Govern Event Page Under Home

- [x] 将 `application/ui/controller/event/` 治理为 `application/ui/controller/home/event_page/`，按页面模板保留文件、类名和行为。
- [x] 同步主页、导航、业务、测试、工具和文档中的当前导入路径。
- [x] 将活动入口动作整合到 `application/ui/navigation/event.py`，不把跨页导航塞回活动页面控制器。
- [x] 完成旧路径扫描、import smoke、compileall、focused 回归和 `git diff --check`。
- **Status:** complete

### Phase 23: Battle Page Map Governance and Aggregation

- [x] 将原 controller/map 聚合页迁移到 operations/sortie_page/battle_page，保留五个顶部标签 Mixin 组合。
- [x] 将地图标题 OCR 识别模型、解析和 OCR 调用归入 battle_page/recognition.py；data.py 只保留面板与章节数据。
- [x] 将地图聚合页和普通出征实际使用的校准收拢到 battle_page/constants.py，并保留旧 common 校准作为兼容入口。
- [x] 同步导航注册、导航图、运行时、业务、测试、工具和文档导入；MAP 仍由导航器注册和寻路。
- [x] 完成 Mixin import/MRO smoke、地图/战役回归 53 passed、check_sortie_api、compileall、旧路径扫描、目标 pre-commit 和 git diff check。
- **Status:** complete

### Phase 24: Shared Top Tabs Ownership

- [x] 确认 top_tabs 同时服务 battle_page、build_page、intensify_page、friend_page 和 mission_page。
- [x] 将 shared/tabbed_page.py 重命名为 shared/top_tabs.py，保留 TabbedPageType 和既有公开函数。
- [x] 同步所有生产、测试、工具和文档引用，确认不归入 sortie_page，避免出征域反向承载侧边栏能力。
- [x] 完成共享标签回归 74 passed、compileall、消费者 import smoke、旧路径扫描、目标 pre-commit 和 git diff check。
- **Status:** complete

### Phase 25: Decisive Page Aggregation

- [x] 将 `controller/decisive/` 迁移到 `operations/sortie_page/decisive_page/`，保留文件名、类名和行为。
- [x] 同步决战页面包、地图顶部标签、导航、业务、测试和工具的导入路径与模块说明。
- [x] 验证新包导出、import/MRO、旧路径扫描、focused 测试、compileall 和差异检查。
- **Status:** complete

### Phase 26: Decisive Controller Second Governance

- [x] 按 UI Controller 规范重整 `decisive_page` 的页面执行、OCR 识别、浮层状态和
  私有校准边界；允许新增职责模块，不修改决战选船算法。
- [x] 将页面专属校准固化到 `decisive_page/constants.py`，保持归一化坐标和业务注释。
- [x] 统一决战页面状态读取和动作命名/顺序，同步所有生产、测试和工具调用方。
- [x] 完成 focused 回归、结构/import/compile/pre-commit/diff 检查，并记录上下文/OCR
  遗留项到既有 TODO 台账。
- **Status:** complete

### Phase 27: UI Controller Shared Area and Feature Porting

- [x] 创建长任务书并明确阶段、反复重读、验收和交付规则。
- [x] 阶段一：迁移 `start_screen.py` 为 login，并盘点/整合 `controller/shared/` 公共能力。
  - [x] 完成登录入口、校准、签名、OCR 边界和调用方盘点。
  - [x] 完成 login 文件迁移、引用同步和 focused 验证。
  - [x] 完成 shared 公共能力盘点、整合和逐项验证。
  - [x] 完成阶段一复核、TODO 台账同步和阶段报告。
- [x] 阶段二：按两份规范全量 Review、评审导航回退契约并治理 OCR/ROI 边界。
  - [x] 2.1 盘点并分批治理 Controller 文件说明、注释、常量、命名、排序、导出和私有导入。
  - [x] 2.2 盘点页面进入/回退契约和导航器边，形成兼容性评审结论。
  - [x] 2.3 盘点 OCR/ROI 与上下文所有权，按 TODO 台账决定迁移或保留。
  - [x] 完成阶段二复核、TODO 台账同步和报告记录。
- [x] 阶段三：使用 ShiinaKuroko 分支功能移植台账，手工移植最近两日有效功能。
- [x] 阶段四：只读检查决战 debug worktree，产出参考移植计划。
- **Status:** done

### Phase 28: Strict UI Controller Governance Rework

用户已否定此前“阶段二治理完成”的验收结论。本阶段以当前文件树和实际调用方为
事实来源，旧阶段记录只作为历史背景，不作为规范符合性证据；必须重新读取本任务书
和两份规范后进入每一个子项。

- [x] 28.1 逐文件建立真实清单：目录/文件名、页面职责、直接调用方、公共出口、
  `constants.py`、`page.py`、`recognition.py` 边界、函数前缀和 `def` 顺序。
- [x] 28.2 先治理文件和目录命名：所有实际页面组采用明确的 `xx_page/` 结构，
  页面执行器归入 `page.py`；同步全部生产、测试、工具和文档引用，禁止保留无真实
  消费者的过渡别名。
- [x] 28.3 按页面域分批重整职责和代码编排：补齐文件级说明、业务注释、常量语义、
  函数命名/顺序和模块导入边界；不修改 `backyard/bath_page`，不改选船算法，OCR、
  上下文、ROI 和私有 API 风险只更新 TODO 台账。
- [x] 28.4 每批完成后执行直接调用方导入 smoke、compileall、focused 验证、目标
  pre-commit 和 `git diff --check`；形成严格返工报告，未验证行为不得标记完成。
- **Status:** done

### Phase 29: Vertical Sortie Page Split

用户确认 `top_tabs` 应升级为 `sortie_page/main_page`，并要求 `sortie_page/` 最终只保留
`main_page`、`battle_page`、`campaign_page`、`decisive_page`、`exercise_page` 和
`expedition_page` 六个页面目录。取消 `MapPage` 的五个 Mixin 聚合，按垂直页面管理能力；
函数只在真实消费者需要时作为页面公开入口，其余实现私有化。

- [x] 29.1 盘点当前六类页面、现有聚合器、公共地图壳和全部生产/测试/工具消费者，确认
  `battle_preparation_page` 与 `sortie_page` 的最终边界；确认准备页迁为
  `operations/battle_preparation_page`。
- [x] 29.2 将 `shared/top_tabs.py` 迁移为 `sortie_page/main_page/`，承载 sortie 页面
  壳识别、顶部标签读取/切换和通用返回；不保留旧聚合入口。
- [x] 29.3 将普通出征章节/地图能力垂直迁入 `battle_page/`，将战役、决战、演习、远征
  能力分别留在对应页面；迁移相关 `constants.py`、`data.py`、`recognition.py`。
- [x] 29.4 删除 `MapPage` 和 `sortie_panel.py` / `decisive_panel.py` 聚合关系，改为
  具体页面之间的直接调用；同步所有消费者和稳定包出口。
- [x] 29.5 按两份规范复核文件职责、函数命名/顺序、私有导入和导航回退；不修改
  `backyard/bath_page`，OCR、上下文和选船风险只记录 TODO。
- [x] 29.6 分阶段执行 import smoke、compileall、focused 回归、目标 pre-commit 和
  `git diff --check`；每完成一个阶段重新读取本任务书并记录未执行验证。
- **Status:** complete

### Phase 32: Fleet F10 Final Acceptance

- [x] 删除旧 Fleet 目录、Mixin、动态代理、旁路状态、旧测试和无消费者决战换船开关。
- [x] 收紧 Fleet 根入口、选船返回 checker、初始快照所有权、导入别名和包出口。
- [x] 完成旧路径、私有导入、循环依赖、配置归属、common 反向依赖和生产深层导入扫描。
- [x] 完成 `230 passed`、compileall、根入口/导航 smoke、`tools/check_sortie_api.py`、
  scoped pre-commit 和 `git diff --check`。
- [x] 产出 `meta/[报告]fleet业务流程重构综合报告.md`，列明未执行的实机 E2E 和后续边界。
- **Status:** complete

## Decisions

| Decision | Rationale |
|----------|-----------|
| 三个页面作为 `backyard` 下的同级页面包 | 它们属于同一 UI 业务域，但 Bath/Canteen 不是 BackyardPage 的内部实现。 |
| 后院主控制器目录命名为 `main_page` | 与现有母港 `controller/home/main_page` 通过包路径区分。 |
| 不新增空 `recognition.py` | Canteen 和 Backyard 当前没有 OCR 专属代码。 |
| 母港主页目录命名为 `home` | 该 Controller 是真实母港主页；`PageName.HOME` 与模板资源 `Templates.MainPage` 仍是稳定业务/资源名称。 |
| 主页校准移入 `home_page/constants.py`，保留 `main.yaml` | Controller 不再依赖通用校准访问器；`main.yaml` 仍被通用坐标测试和潜在外部调用契约使用，不能静默删除。 |
| 母港主页目录简化为 `home` | `HomePage` 已符合其他页面的“业务名 + Page”类命名；目录是包路径，不必重复 `_page` 后缀。 |

### Phase 11: Home Page State Naming

- [x] 将页面状态统一为 `PageName.HOME`，保留枚举值“主页面”。
- [x] 同步导航图、运行时、业务、测试、工具和文档调用方。
- [x] 不改 `Templates.MainPage`、`HomePage` 或外部字符串契约。
- **Status:** complete

### Phase 12: Mode-Specific Bath Navigation

- [x] 在当前 `application.ui.navigation.service` 增加普通出征到澡堂的显式路线。
- [x] 增加决战暂离保存后到澡堂的显式路线，必须使用 `confirm_leave`。
- [x] 移除无法区分来源的通用 `BATTLE_PREP -> MAP` 图边；活动路线后续已由阶段三专用服务接入。
- [x] 从 `application.ui.navigation` 公开导出两条路线并增加最小专项测试。
- [x] 完成 focused pytest、AST/compile 和 `git diff --check`。
- **Status:** complete

### Phase 10: Home Package Path Simplification

- [x] 将 `controller/home/main_page_page/` 重命名为 `controller/home/main_page/`。
- [x] 同步生产、测试、工具、文档和任务记录中的 `home_page` 包路径。
- [x] 保留 `HomePage`、`PageName.HOME`、`Templates.MainPage` 和页面内部文件结构。
- [x] 完成 import smoke、focused pytest、AST/compile 和 `git diff --check`。
- **Status:** complete

### Phase 13: Semantic Page Navigation Names

- [x] 将运行时 `go_main_page` 统一为 `go_home_page`。
- [x] 将主页动作统一为 `go_to_backyard`、`go_to_sidebar`，并将 `Target.HOME` 改为 `Target.BACKYARD`。
- [x] 同步运行时、测试、文档和主页导航调用方。
- [x] 完成 focused pytest、AST/compile 和 `git diff --check`。
- **Status:** complete

### Phase 14: Campaign Bath Navigation

- [x] Add a named campaign formation-to-bath navigation service route.
- [x] Return through the campaign selection MapPage, then home, backyard, and bath.
- [x] Trigger the route from campaign manual-repair detection.
- [x] Keep automatic repair and non-campaign battle flows unchanged.
- [x] Add focused route and campaign-operation tests; 204 related tests passed.
- **Status:** complete

### Phase 15: Manual Bath Repair Termination Integration

- [x] Inspect the merged `cce7121` behavior and map it to the upgraded layers.
- [x] Add a terminal manual-repair exception and dispatch target ships in bath.
- [x] Adapt campaign, normal-sortie, and decisive-sortie callers.
- [x] Stop the active scheduler/API task without consuming remaining rounds.
- [x] Add focused tests and verify the accumulated dirty worktree.
- **Status:** complete

## Errors

| Error | Attempt | Resolution |
|-------|---------|------------|
| 完整 pre-commit 首次暴露受影响 E2E 工具的既有 Ruff 问题 | 1 | 只补类型注解、文件级 E402 例外和已验证的回退日志，重跑后受影响文件通过。 |
| 初次恢复文档时 `git show` 缺少 `autowsgr/application/ui/controller/` 前缀 | 1 | 修正仓库路径映射；未覆盖整文件，只恢复函数级说明。 |
| 文档补齐脚本错误识别 NumPy `Returns` 分隔线 | 2 | 依据逐行标题建立新判定，仍发现泛化文案后停止脚本并从 HEAD 恢复。 |
| 文档恢复映射漏处理 `battle_preparation_page` 通用前缀 | 1 | 单独按目录后缀映射并恢复类/顶层函数说明。 |
| 准备页短词替换重复命中已改名方法 | 1 | 精确恢复 `open_quick_supply`/`open_quick_repair`，不再对整文件短词替换。 |
| 选船短词替换重复命中 `click_remove_ship` | 1 | 精确恢复方法定义和内部调用，并扫描重复符号。 |
| 决战编队重命名后遗留旧模块导入导致测试收集失败 | 1 | 将 `fleet_change.decisive` 改为 `decisive_fleet`，回归恢复。 |
| 最终任务状态复合补丁因计划文件上下文变化失败 | 1 | 拆分为状态、R.4、报告、findings 和 progress 小补丁。 |
| 严格 Controller AST 清单首次使用了嵌套 f-string 引号 | 1 | 改用 PowerShell here-string 传递标准库 AST 清单，未产生文件变化。 |
| 分组 AST 清单首次把 PowerShell 环境变量文本写入 Python 表达式 | 1 | 改为在主进程中替换固定分组名后执行只读清单，未产生文件变化。 |
| 旧路径扫描首次使用了 ripgrep 不支持的 look-ahead 正则 | 1 | 改用 `--pcre2` 或无 look-around 的精确词项扫描，未产生文件变化。 |
| 文档/API 补丁首次误指向共享主仓库而非绑定 worktree | 1 | 改用绑定 worktree 绝对路径重新应用，首次补丁未产生文件变化。 |
| 选船包路径机械替换重复命中已改名路径 | 1 | 精确修正 `choose_ship_page_page_page`，并完成旧路径扫描。 |
| 选船包级导出首次从 constants 导入尚未移动的派生映射 | 1 | 从现有 `base.py` 导出 `CLICK_PANEL`/`PANEL_PROBE`，不复制常量。 |
| 选船 import smoke 首次调用不存在的 `register_pages` | 1 | 读取 registry 实际出口并改用 `register_default_pages`。 |
| 快捷面板方法的全局替换误改公共校准键和业务说明 | 1 | 恢复 `quick_supply`/`quick_repair` 配置键，仅保留 Controller 方法名。 |
| 恢复误改配置键的复合补丁首次因文档上下文不匹配失败 | 1 | 拆分为配置文件精确补丁和单行文档机械修正。 |
| 演习页 OCR 占位方法的复合补丁首次因编码上下文不匹配失败 | 1 | 先精确改方法名，保留占位实现交由 OCR 专题处理。 |
| 任务识别改名补丁首次对同一文件执行两个 Update 操作 | 1 | 合并为单个文件操作后同步 `read_all_mission_names`。 |
| 结构 lint 补丁首次混入占位文件路径 | 1 | 拆分为真实工具文件的小补丁。 |
| 全量 pre-commit 首次被工具既有 lint 和自动修正拦截 | 1 | 补充受影响 E2E 工具的最小类型/例外标注，重跑后全量受影响文件通过。 |
| `apply_patch` rejected a combined Delete/Add operation for the same file | 1 | Use in-place update hunks instead of replacing a file in one patch. |
| In-place sidebar page patch used stale checker names after a prior functional patch | 1 | Read current sections and apply smaller context-specific hunks. |
| Sidebar documentation patch used a stale docstring line after earlier edits | 1 | Apply single-purpose hunks or replace files in separate atomic steps. |
| Intensify page patch used a stale section-header width | 1 | Split the switch-method, mapping, and section-header updates into separate hunks. |
| Public calibration files were already removed before a repeated `git rm` | 1 | Treat the missing path as an already-completed deletion and continue without retrying. |
| One-line AST structure check used invalid generator-raise syntax | 1 | Replace it with explicit `actual`/`expected` dictionaries and an `assert`. |
| A path typo caused an intensify E2E patch to target the old worktree | 1 | Correct the path before applying the final hunk. |
| Sidebar E2E batch patch used a mismatched indentation context | 1 | Inspect actual lines and apply per-file/per-line replacements. |
| AST structure check used invalid one-line comprehension syntax twice | 2 | Replace it with a valid dictionary comprehension; structure check then passed. |
| Runtime import smoke stopped because `pydantic` is not installed | 1 | Record the environment limitation; rely on static/compile validation without adding dependencies. |
| Sidebar line-width check found one 102-column export import | 1 | Split the import across multiple lines; the final line-width check passed. |
| Target pytest hit a permission error in the system temp directory | 1 | Re-ran with an ignored worktree-local `--basetemp` after creating its parent; 206 tests passed. |
| First worktree-local `--basetemp` attempt lacked the `.tmp` parent directory | 1 | Created the ignored parent directory and reran the command successfully. |
| 任务页目录路径验证首次使用了错误的 `parents` 索引 | 1 | 改为直接验证 recognition 文件路径；任务库实际路径确认正确。 |
| 系统环境没有 `pre-commit` 命令 | 1 | 改用锁定环境执行 `uv run --locked --dev pre-commit`。 |
| 锁定环境的 pre-commit 首次运行由 Ruff 自动修正目标文件 | 1 | 重新运行目标文件钩子后全部通过。 |
| 静态常量 parity 首次发现限时标签纵坐标末位精度差异 | 1 | 对比旧校准结果定位并修正为 `0.05694444444444444`，逐项 parity 通过。 |
| `sortie_page` 聚合后直接导入子模块触发 `map`/Mixin 循环 | 1 | 将 `map.__init__` 的 `MapPage` 改为惰性导出，保留公开导入名并通过直接导入 smoke。 |
| scoped pre-commit 发现惰性 `MapPage` 未在 `__all__` 静态声明 | 1 | 增加 `TYPE_CHECKING` 导入声明，运行时惰性行为不变。 |
| 读取战役任务书时误发一次无效工具调用 | 1 | 未产生文件变化，改用正确读取命令继续。 |
| 最终结构断言首次把 `__pycache__` 计入旧目录 | 1 | 忽略缓存目录后重新验证，`sortie_page` 结构检查通过。 |
| 三个 sortie 子模块首次批量检查命令少了路径引号 | 1 | 改用短分组命令继续，未产生文件变化。 |
| 地图旧专属常量长块补丁上下文不匹配 | 2 | 保留旧地图常量作为兼容面；新三个页面已使用各自常量，不重复尝试删除。 |
| 新 sortie 聚合包直接导入子模块触发 `map`/Mixin 循环 | 1 | 让 `map.__init__` 的 `MapPage` 惰性导出，保留公开导入并通过 smoke。 |
| 新子模块 pre-commit 首次由 Ruff 自动修正 6 个问题 | 1 | 重新运行目标钩子后全部通过。 |
| 三个子模块样板拆分期间地图旧常量清理补丁未匹配 | 2 | 不覆盖已有地图改动；保留旧条目兼容，新页面使用各自静态常量并完成 parity。 |
| Phase 25 初始计划补丁使用了过时的阶段上下文 | 1 | 读取当前计划行号后以更小上下文重新登记并完成阶段收尾。 |
| 决战发现记录首次误匹配 progress 的同名历史标题 | 1 | 按 findings 实际尾部定位后单独追加记录。 |
| 决战校准 parity 检查脚本调用不存在的 `ROI.as_tuple()` | 1 | 改用项目实际 API `ROI.to_tuple()`，校准 parity 通过。 |
| 地图页方法顺序补丁首次重复追加三个方法 | 1 | 用 AST 核对方法名并删除副本、恢复唯一且有序的方法组。 |
| 批量追加交付记录的 PowerShell 嵌套引号解析失败 | 1 | 改用逐文件 `apply_patch` 追加，记录内容已完成。 |
| 最终结构审计命令的 PowerShell 嵌套引号解析失败 | 1 | 拆成短 AST 检查命令，结构和顺序审计通过。 |
| 坐标格式审计命令的正则引号解析失败 | 2 | 改用无嵌套引号的边界检查和 `rg`，常量格式审计通过。 |
| login import smoke 首次把四位坐标误当作无限精度值比较 | 1 | 改为比较 1280x720 映射像素；静态坐标 parity 通过。 |
| login 测试首次放在隐式命名空间目录且缺少 monkeypatch 注解 | 1 | 移到现有 `testing/ui` 测试根目录并补充 `pytest.MonkeyPatch` 注解。 |
| shared focused pytest 首次包含不存在的 `test_controller_migration.py` | 1 | 改为运行已存在的选船/准备页测试，`163 passed`。 |
| shared exports smoke 首次把 `TabbedPageType.MAP.value` 当作字符串比较 | 1 | 按 `PageName` 枚举身份读取并改用真实出口断言。 |
| shared pre-commit 首次由 Ruff format 重排 `choose_ship.py` | 1 | 保留机械格式修正并重新运行目标钩子。 |
| Controller 私有导入 AST 扫描首次因嵌套 f-string 引号解析失败 | 1 | 改用简单字符串拼接输出导入对象，未产生文件变化。 |
| 编队私有导入 pre-commit 首次由 Ruff 自动修正 5 处既有导入/命名格式 | 1 | 保留钩子机械修正并重跑目标钩子；编队回归仍通过。 |
| 任务页/食堂治理验证首次把仅含 E2E 脚本的目录当作 pytest 单元测试 | 1 | 改用 `testing/ui` 实际收集的单元测试，后续回归通过。 |
| 任务页/食堂 pre-commit 首次由 Ruff format 补充 1 个空行 | 1 | 保留机械格式修正并重跑目标钩子。 |
| 2.1 页面治理首轮 pytest 指向仅含 E2E 脚本的目录而无测试 | 1 | 改用 `testing/ui` 实际单元回归，`265 passed`。 |
| Controller 坐标扫描首次使用 PowerShell 不支持的路径通配符 | 1 | 改用 `rg --files`/AST 定位常量文件，未产生文件变化。 |
| 2.1 侧边栏/主页复合顺序补丁因上下文不匹配未执行 | 1 | 读取精确行上下文后保留为后续独立批次，未覆盖已有改动。 |
| 坐标格式批次重复套用已完成补丁导致上下文不匹配 | 1 | 读取当前常量后确认目标值已落地，未产生额外变化。 |
| 坐标候选四位值计算首次误用共享 `AutoWSGR` 根目录 | 1 | 改回当前升级 worktree 后完成计算，未产生文件变化。 |
| 导航专项回归触发 3 个既有架构断言失败 | 1 | 记录旧测试与当前常量/显式路线/来源约束冲突，不回退代码或修改无关测试。 |
| 导航兼容性报告复合补丁首次因 progress 尾部上下文不匹配未执行 | 1 | 拆分为报告、任务书、findings 和 progress 小补丁继续，未产生代码变化。 |
| OCR/ROI 回归首次仍使用旧准备页坐标和 `_detect` 局部 patch 符号 | 1 | 同步测试到页面常量和 `_detect._ocr`，后续回归通过。 |
| OCR/ROI 回归第二次漏替换复合测试中的最后一个 `_fuzzy_match` patch | 1 | 精确补齐测试路径，`264 passed`。 |
| `9b000b4` 首轮 pre-commit 报 `PLR0912` | 1 | 将维修方式分派抽为 `_apply_repair`，目标钩子随后通过。 |
| `9b000b4` 首轮 focused 路由测试替身缺少 `set_repairing` | 1 | 同步测试管理器替身和入口 mock 的新回调契约，第二轮 `175 passed`。 |
| `1d7fca7` 地图旧章节方法删除补丁首次上下文不匹配 | 1 | 按 Ruff 格式化后的精确上下文分两批删除旧实现并重跑地图验证。 |
| 地图文件读取命令首次使用了错误的重复 worktree 路径 | 1 | 修正为当前绑定 worktree，未产生文件变化。 |
| `0577f15` 首轮目标 pre-commit 由 Ruff 自动修正 2 处问题 | 1 | 重跑目标钩子后通过。 |
| 阶段三读取决战枚举时附带了不存在的 `autowsgr/common/types` 目录路径 | 1 | 改用实际 `common/types.py` 文件路径，未产生文件变化。 |
| 阶段三聚合 import smoke 首次误从 `shared` 包导入未公开的 `ChooseShipPage` | 1 | 改用稳定模块出口 `shared.choose_ship.ChooseShipPage`，修正后的 smoke 通过。 |
| 读取带方括号的规范文件首次未使用 `-LiteralPath` | 1 | 改用 `Get-ChildItem` 定位文件对象并以 `Get-Content -LiteralPath` 读取，未产生代码变化。 |
| 首次给 `main_page` / `decisive_page` 应用大上下文补丁时上下文已被前一小批修改 | 1 | 改用精确行号读取后拆成小补丁，未覆盖其他改动。 |
| 系统 Python 导入 smoke 缺少 `cv2` | 1 | 改用项目锁定环境 `uv run --locked`；新页面导入、focused 回归和 API 检查通过。 |
| 首次残留扫描命令使用 PowerShell 7 的 `||` 语法 | 1 | 当前 PowerShell 未启动 `rg`；改用兼容的退出处理方式，未产生文件变化。 |
| 首次合并根包与选船返回修正的补丁上下文与实际文件不一致 | 1 | 补丁未落地；按实际行块拆分为独立小补丁后完成。 |
| 首次导入图检查器的 JavaScript 模板字符串未正确闭合 | 1 | 检查命令未启动；改为顺序执行并使用独立 here-string，源码未受影响。 |
| 配置/API focused pytest 的 basetemp 父目录不存在 | 1 | `128 passed, 12 errors` 均为 setup 路径错误；创建工作区临时目录后改用新 basetemp 重跑。 |
| scoped pre-commit 首轮由 Ruff format 自动修改 1 个 Fleet 文件 | 1 | 接受机械格式化结果，重跑同一范围确认其余钩子。 |
| 项目环境未提供独立 `ruff` 可执行文件 | 1 | 独立 `uv run ... ruff` 无法启动；使用项目实际的 pre-commit Ruff hook 复核。 |
| 首次配置/API focused pytest 的 basetemp 父目录不存在 | 1 | 创建工作区内忽略目录并改用新 basetemp，重跑为 `140 passed`。 |
| 首次 Fleet 根包/选船返回合并补丁上下文不匹配 | 1 | 未产生部分修改；按实际文件行块拆分补丁后完成。 |
| 严格静态门禁初次发现 Fleet import 语义别名 | 1 | 将 `numpy as np`、`UIContext as GameContext` 改为真实名称后重跑。 |
| 最终静态检查复合命令使用 PowerShell 不支持的 `&&` 语法 | 1 | 命令未启动；改用 PowerShell 原生分步执行。 |
| 删除 pytest 临时目录的递归命令使用变量承载目标而被安全守卫拒绝 | 1 | 删除未执行；改用已确认的工作区绝对路径直接处理。 |
