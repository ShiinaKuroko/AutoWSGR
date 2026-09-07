Task ID: `20260830-autowsgr-upgrade`
Task Status: `done`
Next Step: Human review of the accumulated architecture-upgrade worktree.

## Goal

将 UI Controller 按业务域组织到 `application/ui/controller/backyard/`、
`application/ui/controller/sidebar/` 和 `application/ui/controller/home/`，保持页面行为和现有未提交修改不变。

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

- [x] 将 `controller/main_page` 重命名为 `controller/home_page`，并将 `controller.py` 规范为 `page.py`。
- [x] 将 `MainPage` 统一命名为 `HomePage`，同步所有生产、导航、业务、测试和工具调用方。
- [x] 将主页专属校准从通用加载包装下沉到页面 `constants.py`，保留业务状态名 `PageName.HOME`。
- [x] 按规范整理主页、浮层和活动导航的文件说明、绝对导入及函数分区。
- [x] 验证旧路径/旧类名无遗漏，运行 AST/compile、focused 测试和 `git diff --check`。
- **Status:** complete

## Decisions

| Decision | Rationale |
|----------|-----------|
| 三个页面作为 `backyard` 下的同级页面包 | 它们属于同一 UI 业务域，但 Bath/Canteen 不是 BackyardPage 的内部实现。 |
| 后院主控制器目录命名为 `main_page` | 与现有母港 `controller/main_page` 通过包路径区分。 |
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
- [x] 移除无法区分来源的通用 `BATTLE_PREP -> MAP` 图边；活动路线保留 TODO。
- [x] 从 `application.ui.navigation` 公开导出两条路线并增加最小专项测试。
- [x] 完成 focused pytest、AST/compile 和 `git diff --check`。
- **Status:** complete

### Phase 10: Home Package Path Simplification

- [x] 将 `controller/home_page/` 重命名为 `controller/home/`。
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
