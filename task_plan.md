Task ID: `20260830-autowsgr-upgrade`
Task Status: `done`
Next Step: 等待用户 review；不自动提交、合并或清理当前 worktree。

## Goal

将 UI Controller 按业务域组织到 `application/ui/controller/backyard/`、
`application/ui/controller/sidebar/` 和 `application/ui/controller/home/main_page/`，保持页面行为和现有未提交修改不变。

## Scope

- `backyard/main_page/`：后院主页面导航控制器。
- `backyard/bath_page/`：浴室页面控制器及 OCR 规则。
- `backyard/canteen_page/`：食堂页面控制器。
- 更新所有生产、导航和测试导入方。
- `sidebar/` 下管理侧边栏主入口、好友、强化和建造/拆解页面。
- 按两份代码规范重塑整个 `sidebar` 页面域的常量、命名、注释和函数顺序。
- 不修改 BathPage 业务逻辑；不创建空的 recognition.py。

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
