# Progress Log

## 2026-09-07

- **Status:** Phase 1 complete; Phase 2 in progress.
- Confirmed the active Git root and Agent binding for the target child worktree.
- Re-read the applicable AutoWSGR `AGENTS.md` and the UI Controller style document.
- Confirmed existing uncommitted changes in `backyard_page/constants.py`,
  `backyard_page/page.py`, and `canteen_page/page.py`; these must be preserved.
- Audited direct imports and found production, navigation, business, and testing consumers.
- Moved the three page packages into `controller/backyard/` and added the domain package marker.
- Updated all full Controller import paths and moved-package dependency docstrings.
- Confirmed the old full Controller paths and physical path text have no remaining matches.
- Phase 2 and Phase 3 complete; Phase 4 verification in progress.
- The existing `backyard_page`, `bath_page`, and `canteen_page` test directory names remain unchanged because they are test layout, not Controller import paths.
- `backyard` domain package added; the three Controller packages now live under it as `main_page`, `bath_page`, and `canteen_page`.
- Updated 38 full Controller import references across production, navigation, business, tests, and E2E documentation.
- `compileall`, AST parsing, old-path scan, and `git diff --check` passed.
- Runtime import smoke was attempted once and stopped at `ModuleNotFoundError: No module named 'pydantic'`; no dependency was added.
- Phase 4 complete; task is ready for manual review.

## 2026-09-07 Sidebar Controller Reorganization

- User expanded the UI Controller domain grouping to include the sidebar main controller, friend, intensify, and build/destroy page.
- Planned target structure: `controller/sidebar/{main_page,friend_page,intensify_page,build_page}`.
- Moved `sidebar_page.py` to `sidebar/main_page/page.py`, `friend_page.py` to
  `sidebar/friend_page/page.py`, and `intensify_page.py` to
  `sidebar/intensify_page/page.py`.
- Moved the existing `build_page/` package to `sidebar/build_page/` and added
  package exports for all four sidebar pages.
- Updated production, navigation, business, testing, and E2E imports to the
  new paths; retained test directory names and delayed imports.
- Added `sidebar/__init__.py` as a domain marker without eager child imports.
- Verified no old full Controller paths remain; AST, `compileall`, and both
  staged/unstaged `git diff --check` checks passed.
- Runtime import smoke failed at the existing YAML calibration loader because
  the environment lacks `yaml`; no dependency or behavior change was made.
- Phase 5 complete; task is ready for manual review.

## 2026-09-07 Sidebar Style and Ownership Rewrite

- Re-read `[规范]ui-controller-code-style.md` and
  `[规范]navigation-code-style.md` before changing the sidebar domain.
- Added private `constants.py` files for sidebar main, friend, and intensify
  coordinates using normalized `0.xxxx` values with business comments.
- Removed the now-unreferenced common calibration wrappers and YAML files for
  sidebar, friend, and intensify.
- Standardized `check_current_page`, `read_active_tab`, and `select_tab`, and
  synchronized production/navigation/business/test callers.
- Reworked sidebar main, friend, and intensify file docs and function ordering;
  kept build/destroy behavior unchanged and adjusted its page API naming.
- Static structure, coordinate, AST, compile, old-reference, and diff checks
  passed. Runtime import smoke stopped because `pydantic` is unavailable.
- Two AST command attempts had syntax errors; a corrected command passed. A
  sidebar E2E batch patch and one repeated calibration deletion were also
  rejected/obsolete without source loss.
- Phase 6 complete; awaiting manual review.

## 2026-09-07 Sidebar Style Rewrite

- User requested the complete `sidebar` domain be reshaped using the navigation
  and UI Controller style specifications.
- Audited the four page packages and confirmed page-specific sidebar, friend,
  and intensify calibration wrappers/YAML have no consumers outside their pages.
- Planned to keep the four page packages under `controller/sidebar/`, move
  private coordinates into page-local constants, and preserve build/destroy
  behavior.
- Phase 6 started; no sidebar constants or function bodies have been edited yet.
- An initial large `apply_patch` was rejected because it targeted the same path
  with both Delete and Add operations; no files changed in that attempt.
- A follow-up in-place patch was rejected on stale `is_current_page` context after
  the functional rename had already landed; no files changed in that attempt.
- A sidebar documentation patch was rejected on one stale docstring line; no
  files changed in that attempt.
- An intensify-page documentation patch was rejected on a stale section-header
  width; no files changed in that attempt.
- A repeated `git rm` found the three public calibration wrappers already absent;
  the earlier deletion remains the only deletion attempt.
- One AST verification command failed on invalid one-line generator/raise syntax;
  no source files changed and the check will be rerun with simpler assertions.

## Verification

| Check | Result |
|-------|--------|
| Binding verification | Passed for target worktree and nested `meta`. |
| Initial source status | Existing user changes preserved. |
| Package structure and old-path scan | Passed. |
| AST/compile and diff checks | Passed. |
| Runtime import smoke | Not verified; environment lacks `yaml`. |

## Errors

| Error | Resolution |
|-------|------------|
| Runtime import smoke failed with missing `yaml` | Recorded the environment gap; relied on AST/compile checks and did not add a dependency. |

## 2026-09-07 Sidebar Style Rewrite Final

- Final target structure contains `sidebar/main_page`, `sidebar/friend_page`,
  `sidebar/intensify_page`, and `sidebar/build_page`.
- Page-local constants, unified state/action names, function order, file docs,
  and business comments now follow the two requested specifications.
- Removed only the unused sidebar/friend/intensify common calibration wrappers
  and coordinate YAML files; `bath_page` was not modified in this phase.
- Final checks passed: 4-page structure, 22 normalized coordinate constants,
  42-file AST parse, `compileall`, old API/reference scans, line width, staged
  and unstaged `git diff --check`, and binding verification.
- Runtime import smoke remains unverified because the environment lacks
  `pydantic`; no dependency was added. No commit was created.
- Earlier Phase 6 entries in this file are provisional checkpoints; this entry
  reflects the final state after all patches and checks.

## 2026-09-07 Legacy Rule Compatibility Patch

- User requested a manual transplant of flexible legacy enemy-rule spelling
  compatibility; `c5a464c` was inspected read-only and not merged.
- Confirmed `_parse_legacy_condition()` is the shared parser used by the server
  Schema path; no Schema code change is needed.
- Phase 7 started; existing UI migration and sidebar changes remain untouched.

## 2026-09-08 Legacy Rule Compatibility Patch Complete

- Updated `_parse_legacy_condition()` to uppercase legacy conditions and remove
  whitespace inside composite comparison operators.
- Preserved single `=` rejection and `==` acceptance.
- Added seven parser compatibility cases, one explicit single-equals rejection
  case, and two `NodeDecisionRequest` API boundary cases.
- The requested target tests passed with a worktree-local basetemp:
  `206 passed in 3.21s`.
- `uv run --locked --dev python -m compileall` and staged/unstaged
  `git diff --check` passed. `autowsgr/server/schemas.py` was not modified.
- `c5a464c` was not cherry-picked or merged; only the requested compatibility
  behavior was manually transplanted.
- Phase 7 complete; task is ready for manual review.

## 2026-09-08 Remaining UI Controller Audit

- User identified `battle_preparation`, `decisive`, `event`, `map`, and
  `mission_page` as the remaining Controller scope.
- Confirmed the five directories are separate page domains with different
  ownership and risk; they should not be flattened into one parent package.
- Recorded the recommended order `mission_page` → `event` → `decisive` →
  `map` → `battle_preparation`.
- No remaining Controller source files were changed during this audit.

## 2026-09-08 Home Page Rewrite Start

- User selected `controller/home/main_page` as the actual home page and requested the
  canonical name `home_page`.
- Phase 9 started after the remaining-controller boundary audit; no Home Page
  files have been moved or rewritten yet.

## 2026-09-08 BuildPage Section Formatting

- Kept `BuildPage` as one UI page module because its build and dismantle tabs
  share the same screen boundary.
- Added explicit code sections for build atomic actions, dismantle atomic
  actions, build composite actions, and dismantle composite actions.
- Confirmed the change is comment-only; `BuildPage` AST parsing and
  `git diff --check` passed.

## 2026-09-08 Home Page Rewrite

- Re-read the applicable repository rules, the two UI Controller specifications,
  and `[任务书]ui-controller样板重构任务.md` before implementation.
- Moved `controller/home/main_page/` to `controller/home/main_page_page/` and renamed
  `controller.py` to `page.py`.
- Renamed the Controller class and all in-repository consumers from `MainPage`
  to `HomePage`; synchronized the home status prefixes to `check_*` and
  `read_overlay`.
- Moved home page physical calibration actually used by the Controller into
  `home_page/constants.py` with normalized four-decimal coordinates and business
  comments. Kept `PageName.MAIN`, `Templates.MainPage`, and generic calibration
  YAML compatibility unchanged.
- Moved `Target` into `page.py` and `OverlayKind` into `overlays.py`; retained
  `overlays.py` and `event_nav.py` because runtime and page callers use them.
- Updated runtime initialization, navigation, logistics, tests, tools, and direct
  documentation references. `bath_page` was not modified.
- Static verification after the final indentation fixes: AST parsed 173 Python files,
  targeted `compileall` passed, targeted line width passed for home files and direct
  callers, and `git diff --check` passed.
- Ruff check was attempted once and stopped because the environment has no `ruff`
  executable. A first compile attempt found accidental indentation in
  `testing/ui/backyard_page/e2e.py:109` and `tools/e2e/cases/initialize.py:30`;
  both were corrected and the rerun passed.
- Two early multi-file patch attempts were rejected by stale/incorrect context; no
  source was changed by those attempts. One later path typo was rejected before
  applying; all source changes were then applied with smaller patches.

- Re-read the updated task book after resolving its stale done-state and old
  worktree path; the B1 Home Page extension is now the active phase.
- Final home-page import smoke passed, and focused overlay/initialization/startup
  tests passed: `22 passed in 2.86s`.

- Final status: the current task plan and the updated task book both mark the
  UI Controller upgrade task as `done`, with the worktree waiting for manual
  review.

## 2026-09-08 Home Directory Simplification

- Confirmed that `HomePage` matches the existing Controller class naming pattern;
  changed only the package directory from `home_page` to `home`.
- Updated all production, test, tool, documentation, and task-record package paths.
  `PageName.MAIN` and `Templates.MainPage` remain unchanged.
- Final validation passed after the move: `home` import smoke, 22 focused tests,
  AST parsing of 173 Python files, targeted compileall, old-path scan,
  `git diff --check`, cached diff check, and binding verification.
- Two path-sync patch attempts were rejected by stale/incorrect context and one
  contained a duplicated parent path; no source changes were made by those attempts.

## 2026-09-08 HOME State and Bath Route Integration

- Re-read the task instructions and searched the handoff terms before inspecting the
  source worktree. The handoff memory title was not present in Engram, so the supplied
  source files and task records were used as the read-only source of truth.
- Renamed the page enum member `PageName.MAIN` to `PageName.HOME` while keeping the
  value `主页面`; synchronized all discovered aliases, production code, tests, tools,
  docs, and task records.
- Manually adapted the source worktree's mode-specific bath routes into
  `application/ui/navigation/service.py`, exported them from `application/ui/navigation`,
  and added `testing/ops/test_bath_navigation.py`.
- Removed the generic `BATTLE_PREP -> MAP` edge and changed the existing topology test
  to assert that the ambiguous edge is absent. Added an explicit activity TODO.
- First route test run found 17 stack-test failures because `P.MAIN` aliases were not
  included in the initial search; replaced them with `P.HOME`. A subsequent replacement
  temporarily introduced indentation errors in the same test file; restored the original
  4/8-space function-body indentation.
- Final focused verification passed: `97 passed in 3.04s`; AST/compile, old enum/path
  scans, `git diff --check`, and binding verification also passed.
- Ruff/pre-commit/full pytest/real-device E2E were not run for this batch; no new
  dependency or source worktree mutation was made.

## 2026-09-08 Semantic Page Navigation Names

- Renamed the runtime helper `go_main_page` to `go_home_page` and synchronized its
  test and documentation callers.
- Renamed the HomePage actions `go_home` to `go_to_backyard` and `open_sidebar` to
  `go_to_sidebar`; renamed the backyard target from `Target.HOME` to `Target.BACKYARD`.
- Also aligned runtime helper names `is_on_home_page`, `recover_to_home_or_restart`,
  `_is_on_home_page`, and `_wait_for_home_page`; no serialized page value changed.
- Final validation passed: 97 focused tests, semantic naming import smoke, compileall,
  AST parsing, old-name scan, and both staged/unstaged `git diff --check` checks.

## 2026-09-08 Manual Repair Bath Navigation Integration

- Inspected the source worktree and isolated committed `450c88a` from its later
  uncommitted repair/scheduler changes.
- Manually integrated the committed behavior into the current architecture:
  `apply_repair` now accepts a manual-repair callback; normal sorties use the
  normal bath route and decisive sorties use the decisive bath route.
- Activity, exercise, campaign, and decisive-map-internal repair flows were left
  unchanged; the source worktree's later repair batch (`7443018`) was not copied.
- Validation passed: 172 focused tests, targeted compileall, and staged/unstaged
  `git diff --check`.
- Committed as `c8daf9a` (`fix(repair): integrate manual bath termination flow`);
  unrelated dirty and staged UI migration changes remain in the worktree.

## 2026-09-08 Campaign Bath Navigation

- Added `goto_bath_from_campaign_sortie` to the navigation service and public
  navigation exports.
- The route explicitly executes campaign formation → campaign selection
  (`BattlePreparationPage.go_back`) → home (`MapPage.go_back`) → backyard → bath.
- Campaign preparation now passes this route as the manual-repair callback when
  `config.repair_manually` is enabled; automatic repair behavior is unchanged.
- No virtual `PageName.CAMPAIGN` or generic `BATTLE_PREP -> MAP` edge was added;
  campaign selection is the existing `MapPage` battle panel.
- Validation passed: 204 related tests, targeted compileall, and
  `git diff --check`.

## 2026-09-08 Manual Bath Repair Termination Integration

- Manually adapted the merged `cce7121` flow into the upgraded architecture;
  the source commits were `e6d9fee`, `450c88a`, and `7443018`.
- Added terminal `ManualRepairRequiredError`, target-ship bath dispatch with
  runtime state synchronization, and callback wiring for campaign, normal
  sorties, and decisive sorties.
- Added terminal handling to Processor, the legacy scheduler, the direct normal
  HTTP loop, and the decisive state-machine boundary so remaining rounds do not run.
- Campaign now checks the selected fleet for repair before departure and uses the
  campaign-specific return route; activity remains TODO-only and is not adapted.
- Validation passed: 274 related tests, targeted compileall, and staged/unstaged
  `git diff --check`.
- No commit was created; all pre-existing dirty worktree changes remain intact.

## 2026-09-08 Sortie UI Governance S0

- 建立 `meta/[任务书]出征模块治理任务.md`，并将主任务计划的 Phase 16 切换为
  `in_progress`。
- 完成目标目录、公开入口、直接调用方、地图/战斗导航边和选船调用链盘点。
- 结论：`fleet_change` 直接依赖页面坐标、截图、`ChooseShipPage`、`ctx.ocr` 和
  战斗模式编排，当前不能安全下沉到 `common`；保留在 UI 原目录。
- 将出征页 OCR 注入优先级、选船 OCR 所有权和 `_fuzzy_match` 私有 API 依赖写入
  `[todo]` 台账；本批不优化 OCR 或上下文。
- 首次创建任务书的批量 `apply_patch` 因旧阶段标题上下文不匹配被拒绝，文件未改动；
  后续改用小块补丁完成任务书和记录更新。追加 findings 的第二次批补丁也因尾部
  上下文不匹配被拒绝，之后按实际尾行单独完成。
- S0 完成；已重读任务书，下一阶段为 `battle_preparation` 原目录治理。

## 2026-09-08 Sortie UI Governance S1

- 新增 `battle_preparation/constants.py`，将准备页点击、状态颜色、血条和 OCR
  裁剪参数集中到页面域；旧 `common.calibration.battle_preparation` 暂留兼容。
- 将准备页状态入口统一为 `check_current_page`、`read_selected_fleet`、
  `read_active_panel`、`check_auto_supply_enabled` 和 `check_support_enabled`，并
  同步生产、测试和工具调用方。
- 补齐准备页及 `fleet_change` 子包的文件级职责说明，改为绝对导入；没有移动或
  改写选船算法。
- 校准 parity 首次使用四位小数失败；定位为舍入精度差异后恢复 YAML 归一化精度，
  parity 检查通过。
- focused 测试第一次因准备页提前引用未治理的 `MapPage.check_current_page` 失败
  2 项；恢复为当前 `MapPage.is_current_page` 后通过：`201 passed`。
- S1 仍待完成目标文件的格式钩子、全量旧入口扫描和任务书重读。

## 2026-09-08 Sortie UI Governance S1 Complete

- 出征准备页校准已集中到 `autowsgr/application/ui/controller/battle_preparation/constants.py`，
  保留旧 `common.calibration.battle_preparation` 供外部测试/工具兼容。
- 准备页状态入口已统一为 `check_current_page`、`read_selected_fleet`、
  `read_active_panel`、`check_auto_supply_enabled` 和 `check_support_enabled`；所有
  生产、测试和工具调用方已同步。
- `fleet_change` 子包补齐文件级职责说明并改为绝对导入；选船核心没有移动、重命名
  或改写。其 OCR/识别内部命名和私有匹配 API 按 TODO 保留。
- 校准 parity、import smoke、compileall、旧准备页入口扫描和 `git diff --check`
  通过；focused 测试通过：`201 passed`。
- 目标文件 pre-commit 首次自动修正 19 个 Ruff 问题，第二次自动修正 2 个导入问题，
  第三次稳定通过；格式钩子最终全部通过。
- 验证过程中发现准备页提前调用未治理的地图新命名，恢复为当前地图入口后通过；
  该跨阶段命名统一留给 S4。
- S1 完成；已更新任务书，下一阶段为 `decisive` 治理。

## 2026-09-08 Sortie UI Governance S2 Complete

- 新增 `autowsgr/application/ui/controller/operations/sortie_page/decisive_page/constants.py`，统一决战总览、
  地图、浮层和战备舰队的 Controller 校准入口；旧共享校准文件暂留兼容。
- 决战总览页状态入口改为 `check_current_page`，章节和入口状态改为
  `read_stage`、`read_entry_status`；地图控制器的浮层、技能、舰标和战备舰队状态
  入口改为 `check_*`/`read_*`，同步决战业务、导航和测试调用方。
- 浮层模块改为直接提供 `check_decisive_map_page`、`check_fleet_acquisition`、
  `read_overlay_template` 和 `read_overlay_signature`；地图控制器不再从浮层模块
  间接取得坐标常量。
- 补齐决战包、总览页、地图控制器、浮层、舰队 OCR、准备页和旧编队入口的文件级
  职责说明；没有优化 OCR 算法或修改选船实现。
- 决战 focused 测试通过：`8 passed`；决战 import smoke、校准 parity、compileall
  和旧入口扫描通过；pre-commit 最终全部通过。
- 校准 parity 首次直接比较 numpy 数组触发布尔值歧义，改用数组专用比较后通过；
  另有一次已有 `_handle_prepare_combat` 复杂度检查触发，保留原业务结构并增加
  明确的 `C901` 标记，未顺手重构业务处理器。
- S2 完成；已更新任务书，下一阶段为 `event` 治理。

## 2026-09-08 Sortie UI Governance S3 Complete

- 新增 `autowsgr/application/ui/controller/event/constants.py`，收拢活动节点、
  入口、难度和出击浮层校准；活动页面没有专属 OCR，因此没有创建空的
  `recognition.py`。
- `BaseEventPage.is_current_page` 改为 `check_current_page`，难度读取改为
  `read_difficulty`，内部难度/入口检查命名同步；生产、导航、测试和 E2E 调用方已
  更新。
- 保留活动手动维修及 `BATTLE_PREP -> EVENT_MAP -> HOME -> BACKYARD -> BATH`
  TODO，不虚构活动返回导航。
- 活动校准 parity、import smoke、compileall、旧入口扫描和目标 pre-commit 通过；
  活动页面及普通出征相关 focused 测试通过：`181 passed`。
- 曾因额外带入旧 `testing/ui/main_page/e2e.py` 的两个无关 lambda lint 问题导致一次
  钩子失败；缩小到本阶段文件集后通过，未修改该无关问题。
- S3 完成；已更新任务书，下一阶段为 `map` 治理。

## 2026-09-08 Sortie UI Governance S4 Complete

- 新增 `autowsgr/application/ui/controller/operations/sortie_page/battle_page/constants.py`，收拢地图、普通出征、
  战役、演习和远征面板的 Controller 校准；旧共享校准文件和 `common.vision.map`
  的 OCR 入口暂留兼容。
- `BaseMapPage` 状态入口改为 `check_current_page`、`read_active_panel`、
  `check_expedition_notification` 和 `read_selected_chapter_y`；面板读取入口改为
  `read_campaign_remains`、`read_difficulty`、`read_acquisition_counts`、
  `read_exercise_rival_status`、`read_ready_expedition_slot` 和
  `read_loot_and_ship_count`，所有直接调用方已同步。
- 补齐地图包、基类、数据、组合页和五个面板的文件级职责说明；保持 Mixin/MRO、
  普通/战役/演习/远征/决战导航行为和 `BATTLE_PREP` 来源约束不变。
- 地图校准 parity、import smoke、全量相关 compileall、旧入口扫描和目标 pre-commit
  通过；地图/远征/战役/演习/结算 focused 回归通过：`257 passed`。
- `tools/e2e_chapter_nav.py` 因既有 E402、复杂度、类型注解和宽泛异常问题未纳入
  pre-commit 修复；本批只同步其地图检查入口，问题留在报告，不改脚本结构。
- S4 完成；已更新任务书，下一阶段为 `home/event_nav.py` 治理。

## 2026-09-08 Sortie UI Governance S5 Complete

- 审查 `autowsgr/application/ui/controller/home/main_page/event_nav.py`，其文件级说明、绝对
  导入、活动导航命名和私有辅助函数编排已符合当前规范，无需增加代码。
- 保持活动入口点击、浮层清理、目标页面确认和重试行为不变；活动出征返回澡堂
  TODO 仍由活动/导航边界负责。
- home event navigation import smoke、compileall、目标 pre-commit 和 `git diff --check`
  通过。
- S5 完成；已更新任务书，下一阶段为 S6 统一审查与交付。

## 2026-09-08 Sortie UI Governance S6 Complete

- 完成目标模块统一审查并生成 `meta/[报告]出征模块治理综合报告.md`。
- 选船模块确认保留在 UI 原目录；四个 Controller constants 入口、状态命名、直接
  调用方和文件级说明已全部落地。
- 上下文/OCR问题继续留在两个 `[todo]` 台账；无 `bath_page` 本批改动。
- 最终合并 focused 回归通过：`319 passed`；目标源码/调用方 scoped pre-commit、
  compileall、import smoke、四组校准 parity 和 `git diff --check` 均通过。
- Ponytail 审查列出约 17 行立即删除候选和兼容校准文件后续删除条件，未擅自删除
  潜在外部入口。
- `tools/e2e_chapter_nav.py` 只同步地图检查入口，既有独立 lint 问题未处理；报告已
  明确记录，未运行真实设备 E2E 或完整全量 pytest。
- S6 完成，任务书待更新为 `done` 并重读确认。

## 2026-09-08 Operations Aggregation Complete

- 按用户确认的四区域模型新增 `autowsgr/application/ui/controller/operations/`，
  将 `mission_page` 完整迁移到 `operations/mission_page/`。
- 同步任务页面内部导入、主页、导航注册/图、奖励业务、测试和文档路径；保留
  `MissionPage`、`PageName.MISSION` 和原页面结构。
- `operations/__init__.py` 仅表达目录归属，不增加子页面聚合导出；真实入口为
  `application.ui.controller.operations.mission_page`。
- 迁移后的重复常量导入和 `CLICK_BACK` 隐式导出问题已修正，未改变识别或操作逻辑。
- 验证通过：operations import smoke、任务路由 `36 passed`、compileall、旧路径扫描、
  scoped pre-commit 和 `git diff --check`。
- 四区域当前状态：`home`、`backyard`、`sidebar`、`operations`；本阶段未移动
  `home/backyard/sidebar` 或其它页面组。任务计划已更新为 `done`。

## 2026-09-08 PageName Semantic Naming Audit

- 读取 `PageName` 定义、页面注册表、导航图、运行时、业务、测试、工具和文档调用方。
- 确认当前共有 15 个成员；`HOME` 已是主页状态的唯一成员，所有枚举值保持现状。
- 确认 `CHOOSE_REPAIR` 没有仓内调用方，实际对应浴室页面上的修理浮层，不属于独立页面状态。
- 提出候选统一映射：`BATTLE_PREP -> BATTLE_PREPARATION`、`DECISIVE_BATTLE -> DECISIVE`、
  `EVENT_MAP -> EVENT`、`CHOOSE_SHIP -> SHIP_SELECTION`；其余成员暂不改名。
- 尚未修改任何 `PageName` 成员或调用方，等待用户确认候选映射；避免误伤外部 Python API。

## 2026-09-08 Mission Page Module Split

- 将 `MissionPanel`、`PANEL_LIST` 和页面侧 `CLICK_PANEL` 派生映射移入
  `autowsgr/application/ui/controller/operations/mission_page/page.py`。
- 新增 `mission_page/constants.py`，集中任务页返回、标签、颜色、OCR 裁剪、按钮扫描和
  列表滚动参数；保留现有校准读取方式和数值。
- 将 `ButtonType`、`MissionInfo`、任务库读取、进度正则和任务 OCR 识别移入
  `mission_page/recognition.py`；修正迁移后任务库路径到 `autowsgr/common/data/missions.yaml`。
- 更新 `mission_page/__init__.py` 的稳定导出并删除职责混杂的 `data.py`；没有修改外部
  任务页面调用方、PageName、bath_page 或页面业务流程。
- 验证通过：目标目录 compileall、任务库 import smoke、旧生产导入扫描、目标文件锁定环境
  pre-commit，以及 `uv run --locked --dev pytest -q testing/ui testing/ops/test_scheduler_unit.py` 的
  `296 passed`；`git diff --check` 通过。
- 系统级 `pre-commit` 命令不存在，已使用项目锁定环境替代；首次 Ruff 自动修正后再次运行钩子通过。

## 2026-09-08 Sortie Page Aggregation and Partial Governance

- 新建 `autowsgr/application/ui/controller/operations/sortie_page/`，迁入原地图顶部标签的
  `sortie.py`、`exercise.py`、`campaign.py`、`expedition.py` 和 `decisive.py`。
- 普通出征和决战按用户要求只迁移文件；演习、战役和远征完成本轮规范治理，未改变业务算法。
- `MapPage`、地图包、工具和当前文档导入已同步到新路径；`map/__init__.py` 改为惰性导出
  `MapPage` 以消除直接导入时的循环，公开导入兼容保持不变。
- 验证通过：五个 Mixin import/MRO smoke、`tools/check_sortie_api.py`、相关 compileall、
  旧路径扫描、scoped pre-commit、`git diff --check`，以及演习/战役/远征相关回归 `108 passed`。
- 一次 pre-commit 发现惰性导出缺少 `__all__` 静态声明，已用 `TYPE_CHECKING` 修正后稳定通过；
  未将普通出征和决战文件纳入格式钩子，确保其只发生文件迁移。
- 最终结构检查首次把 `__pycache__` 误计入旧目录而失败，修正断言后通过；该检查失败未产生源码变化。

## 2026-09-08 Sortie Submodule Template Split

- 将 `sortie_page/exercise.py`、`campaign.py`、`expedition.py` 分别迁移为
  `exercise_page/page.py`、`campaign_page/page.py`、`expedition_page/page.py`。
- 新增三个子目录的 `constants.py`；演习和远征没有真实 OCR，因此按规范不创建空
  `recognition.py`。
- 新增 `campaign_page/recognition.py`，迁移战役次数/获取数量 OCR、解析和结果模型；页面
  执行器只负责面板切换、难度操作和出征入口。
- 更新三个子包和 `sortie_page/__init__.py` 的稳定导出；普通出征和决战入口文件没有内容治理。
- 任务书重读后将 S8 标记完成；地图旧专属校准条目暂保兼容，后续再做清理审计。
- 验证通过：三组常量 parity、子包 import/export/MRO smoke、compileall、旧路径扫描、
  scoped pre-commit、`git diff --check`，以及演习/战役/远征相关回归 `108 passed`。

## 2026-09-08 Mission Constants Ownership Correction

- 根据复核意见，将 `mission_page/constants.py` 从动态读取 `common.calibration` 改为纯静态
  页面数据模块，移除所有下层导入；保留旧公共校准文件作为未触碰的外部兼容文件。
- `recognition.py` 在识别边界内将本页 RGB/ROI 元组转换为 `Color` 和 `ROI`，不改变按钮扫描
  或 OCR 结果；静态值与旧校准结果逐项 parity 通过。
- 首次 parity 定位到限时面板纵坐标末位误差并已修正；随后目标 pre-commit 和相关回归均通过：
  `296 passed`。

## 2026-09-08 PageName TODO Ledger

- 新增 `meta/[todo]PageName语义统一.md`，记录当前 15 个成员、四个候选改名、
  `CHOOSE_REPAIR` 浮层边界和后续兼容验证要求。
- 按用户要求暂不修改 `PageName` 源码、调用方、枚举值或页面行为；命名统一延期到后续专题。

## 2026-09-08 Sortie Submodule Split Final Record

- 复读出征任务书确认 S8 完成；三个子模块已按规范拆分，普通出征和决战保持仅迁移文件。
- 地图旧专属常量清理因已有文件上下文不匹配未执行，保留兼容条目；新目录使用独立静态常量。

## 2026-09-09 Event Page Governance

- 将活动页面保留在 controller/home/event_page，文件结构为
  __init__.py、constants.py 和 page.py；没有创建空 recognition.py。
- 将活动页面专用坐标、颜色和 ROI 固化到 event_page/constants.py，所有点击坐标统一为
  四位归一化值，并校验四位值在 1280x720 下保持原基准像素。
- 按页面规范整理 page.py 的页面检查、状态读取、浮层关闭、页面选项、出击组合动作、
  页面返回和私有识别辅助顺序；select_node、select_difficulty、select_entrance、
  close_node_overlay 使用统一业务前缀。
- 将原 event_nav.py 迁移到 application/ui/navigation/event.py，改为接收 GameContext；
  COMMON_EDGES 的 HOME -> EVENT_MAP 边和 HomePage 共用同一导航实现，移除无效
  is_base_page 参数。
- 新增活动导航边 wiring 测试；活动页 focused 回归 15 passed，导航边测试 1 passed，
  import smoke、compileall、坐标基准像素 parity 和 git diff --check 通过。
- 架构总测试仍有 3 个既有断言失败，分别涉及 battle_preparation/constants.py、导航
  服务旧函数集合和已移除的通用战斗边；本次未修改这些无关测试。
- 首次目录迁移命令因 PowerShell 的只读变量名冲突失败，源目录未变化；改用明确变量名
  后完成，未造成代码丢失。
- 一次旧路径扫描命令因未启用 rg 的 PCRE2 look-ahead 解析失败；改用 --pcre2 重跑并
  通过，未产生文件变化。

## 2026-09-09 Home Area Nested Main Page Correction

- 根据用户最终确认，保留 controller/home 作为主页区域目录，在其下新增
  controller/home/main_page，并将主页的 __init__.py、constants.py、overlays.py 和
  page.py 下沉其中；event_page 与 main_page 同级。
- 新增 home/__init__.py 作为区域级稳定导出；HomePage、PageName.HOME 和页面行为不变。
- 将所有此前指向顶层 controller/main_page 的当前引用同步为
  controller.home.main_page 或 controller.home.event_page；顶层 main_page 路径扫描干净。
- 回归通过：嵌套 home import/navigation smoke、compileall、活动/导航/主页浮层相关
  23 passed、目标 pre-commit（首轮 Ruff 修正后重跑通过）、旧路径扫描、git diff
  --check 和绑定校验。

## 2026-09-09 Battle Page Map Governance

- 将原 controller/map 聚合页迁移到 operations/sortie_page/battle_page，保留
  base.py、page.py、constants.py、data.py 和新增的 recognition.py。
- 将地图标题 MapIdentity、文本解析和 OCR 调用归入 recognition.py；BaseMapPage 的
  页面读取入口统一为 read_map，普通出征及工具调用方已同步。
- 将地图聚合页与普通出征实际使用的校准固化到 battle_page/constants.py，重复的
  演习/战役/远征专用常量继续由各自子页面所有；旧 common 校准保留兼容。
- MapPage 仍属于 UI Controller；MAP 页面状态注册和 HOME/MAP 等跨页边继续由
  application/ui/navigation 维护，导航器只调用 battle_page 的公开动作。
- 同步运行时、业务、导航、测试、工具和文档引用；旧 controller/map 路径无残留。
- 验证通过：地图/战役/演习回归 53 passed、check_sortie_api、compileall、import/MRO
  smoke、静态坐标 parity、目标 pre-commit（首轮 Ruff 修正后重跑通过）、git diff
  --check 和绑定校验。
- 本阶段未处理旧 common 校准文件删除、上下文/OCR 生命周期优化或普通出征/决战业务算法。

## 2026-09-09 Decisive Page Aggregation Started

- 已确认当前绑定 worktree 和目标分支，保留现有脏改动。
- 已盘点决战页面组 8 个文件及所有旧导入路径；`sortie_page/decisive.py` 不在迁移范围。
- 已登记主任务 Phase 25，完成目录迁移和引用同步，下一步进行结构及 focused 验证。

## 2026-09-09 Shared Top Tabs Rename

- 根据调用方审计，tabbed_page.py 同时服务出征、侧边栏和任务页面；未将它错误归入
  sortie_page，而是重命名为 shared/top_tabs.py。
- 同步 battle_page、mission_page、sidebar/build_page、intensify_page、friend_page、
  common vision 文档和所有相关测试引用；TabbedPageType 及公开函数行为保持不变。
- 共享标签回归 74 passed，消费者 import smoke、compileall、旧路径扫描、目标
  pre-commit（首轮自动修正后重跑通过）、git diff check 和绑定校验通过。
- 首次 import smoke 的断言误把 PageName 枚举成员与中文字符串比较，模块导入未受影响；
  改为枚举身份校验后通过。
- 读取旧地图校准值时一次 Python 命令误混入 PowerShell 语句，另一次查询了不存在的
  campaign/expedition/map 坐标文件；改用有效的 battle_page 模块和既有 map 校准入口
  完成 parity，未产生源码变化。

## 2026-09-09 Decisive Page Aggregation Complete

- 将 `controller/decisive/` 整体迁移到
  `controller/operations/sortie_page/decisive_page/`，保留 8 个文件、类名、公开导出
  和业务行为。
- 同步生产、导航、业务、测试、工具和治理文档中的旧导入路径；保留
  `operations/sortie_page/decisive.py` 顶部标签 Mixin。
- 验证通过：决战包 import/export/MRO smoke、目标 compileall、旧路径扫描、
  focused `142 passed`、目标 pre-commit 和 `git diff --check`；绑定校验通过。

## 2026-09-09 Decisive Controller Second Governance Complete

- 按两份规范完成决战页面组职责治理：静态私有校准、总览 `page.py`、地图 `map_page.py`、
  纯 OCR `recognition.py`、浮层视觉识别和准备页适配均已归位。
- 删除无消费者的旧重复入口，统一页面状态读取命名和地图页 `def` 顺序；保留
  `DecisiveBattlePage`、`DecisiveBattlePreparationPage`、`DecisiveMapController` 公共导出。
- 未修改 `bath_page`、决战选船算法或业务状态机策略；OCR/上下文生命周期问题写入
  既有 TODO 台账。
- 验证通过：校准 parity、结构/import smoke、compileall、focused `163 passed`、
  目标 pre-commit 和 `git diff --check`。

## 2026-09-09 Login Module Migration Complete

- 已重读任务书后完成 `start_screen.py` 到 `controller/login/` 的迁移，并同步运行时、
  文档和新增的无设备登录页测试。
- 验证结果：login/初始化 focused 测试 `11 passed`；compileall、导入 smoke、
  旧签名/坐标 parity、目标 pre-commit 和 `git diff --check` 通过。
- 已更新任务书 1.1 的结构、引用和验证勾选；下一步重新读取任务书后盘点
  `battle_preparation`、`operations/sortie_page` 与 `shared` 的公共能力。

## 2026-09-09 Shared Area Login Discovery

- 已重读 `[任务书]ui-controller公共区域整合与新功能移植任务.md`，完成登录迁移的
  第一项盘点并更新任务书勾选状态。
- 确认 `start_screen.py` 无 OCR 逻辑；目标为 `controller/login/` 下的
  `__init__.py`、`constants.py`、`page.py`，不创建空识别模块。
- 已定位生产、文档调用方及旧校准/签名来源；下一步重读任务书后实施文件迁移和引用同步。

## 2026-09-09 Shared Method Inventory Round 1

- 已重读任务书并完成 `battle_preparation`、`operations/sortie_page`、`shared` 的
  文件、函数、导出和初步消费者盘点。
- 初步结论：`top_tabs` 可作为既有公共视觉能力继续维护；`choose_ship` 是带 UI/OCR/
  上下文的完整选船页面控制器，暂不下沉；地图导航和模式选船仍需按消费者继续拆分
  归属，未产生代码变更。
- 下一步追踪智能选船、地图操作和标签页的全部调用链，并记录每类能力的状态所有者。

## 2026-09-09 Shared Method Inventory Round 2

- 已追踪标签页与选船公共 API 的全部当前生产消费者、测试消费者和文档引用。
- 已确认 `top_tabs` 已有稳定公共出口；`ChooseShipPage` 是跨普通/战役/决战复用的
  带上下文 UI 控制器，不能把 OCR、坐标或算法复制到新公共模块。
- 发现选船模块使用 `common.vision.ocr._fuzzy_match` 的私有 API，纳入阶段二 OCR/私有
  API 台账；本轮继续读取地图操作和准备页方法，尚未修改代码。

## 2026-09-09 Shared Method Inventory Round 3

- 已读取地图基类、普通出征面板和决战地图控制器的页面动作边界。
- 已确认地图公共基类已经存在于 battle_page；普通/决战的模式差异无法由一个 shared
  方法安全覆盖，继续保留页面所有权并让导航器负责跨页边。
- 下一步扫描全 Controller 重复的 `check/read/click/go_back/change` 入口和所有模式
  消费者，补齐未知共享方法结论。

## 2026-09-09 Shared Area Integration Complete

- 已完成公共能力的全部消费者、重复入口、私有依赖和导航边盘点；确认现有
  `shared/top_tabs.py`、`shared/choose_ship.py` 已是最小公共模块。
- 为两个公共子模块补充 `__all__` 稳定出口；没有新增地图导航或智能选船包装，
  避免跨页面状态、模式策略和 `GameContext` 所有权被隐藏耦合。
- 验证结果：选船/准备页 focused `163 passed`，shared 导出 smoke、目标 compileall、
  目标 pre-commit 和 `git diff --check` 通过；期间两次错误命令已写入任务计划 Errors。
- 已更新任务书 1.2 全部勾选；下一步重读任务书，执行阶段一复核并整理上下文/OCR/ROI
  TODO 与非视觉问题报告，然后再进入阶段二。

## 2026-09-09 Phase 1 Complete

- 已完成阶段一复核，写入阶段报告并同步上下文/OCR TODO；任务书 1.1、1.2、1.3
  全部完成，阶段二待开始。
- 阶段一验证基线：login/初始化 `11 passed`，选船/准备页 `163 passed`；目标导入、
  compileall、坐标/签名 parity、pre-commit 和 `git diff --check` 通过。
- 下一步按新任务书重新读取后开始阶段二的全量 Controller 规范 Review。

## 2026-09-09 Stage 2 Controller Review Inventory

- 已读取整个 Controller 文件清单并完成首轮 AST/文本审计：文件级说明完整，
  方法顺序、旧命名、坐标格式和私有导入是主要治理面。
- 已建立按风险分批的候选文件清单；`bath_page` 仅记录不改既有业务，选船算法和
  OCR 私有 API 不在本轮直接重写。
- 一次私有导入 AST 命令因 f-string 引号解析失败，尚未产生文件变化；下一步用
  简化脚本完成私有对象导入清单，再按页面域治理第一批低风险模块。

## 2026-09-09 Stage 2 Private Import and Ordering Review

- 已完成 Controller 私有对象导入清单和类方法顺序清单；模块级 docstring 没有缺失。
- 已区分 OCR 私有函数问题与编队内部私有模块对象问题：前者进入 2.3，后者可在
  2.1 以模块导入方式修正。
- 已确认页面专属坐标格式、方法前缀和函数顺序需要按页面域分批处理；未修改代码，
  下一步先治理 `battle_preparation` 编队内部私有导入和低风险页面顺序。

## 2026-09-09 Stage 2 Controller Governance Batch A

- 完成任务页/食堂页面命名和顺序治理，并同步 MissionPage 的状态检查调用方。
- 完成 battle_preparation 基类、维修 Mixin 和编队内部私有对象导入治理；未改选船
  算法、OCR 私有匹配函数或页面业务流程。
- 验证结果：`testing/ui` 回归 `265 passed`，编队/战役/演习回归 `169 passed`；
  目标 compileall、目标 pre-commit 和 `git diff --check` 通过。
- 下一步处理检测 Mixin、地图基类和普通出征/决战页面的剩余函数顺序，继续保持浴室
  页面只审查不改动。

## 2026-09-09 Stage 2 Controller Governance Batch B

- 完成普通出征地图基类和决战总览页的函数顺序治理；地图/决战相关回归 `300 passed`。
- 完成任务页、食堂页、出征准备基类/维修 Mixin 和编队私有模块导入治理；前置回归
  仍通过，未改业务算法。
- 下一步继续处理准备页检测/维修函数顺序、普通出征读取区和侧边栏页面回退顺序，
  然后汇总 2.1 的格式/导入剩余项。

## 2026-09-09 Stage 2 Coordinate Format Audit

- 已完成所有 Controller 常量文件的浮点坐标盘点，确认需治理的长小数主要集中在
  出征准备、地图顶部标签、演习/战役/远征和决战页面。
- 采用四位值保持 1280x720 映射像素不变的验证策略；本阶段先不改 ROI/OCR 参数。
- 下一步分批修改 `battle_preparation/constants.py` 的点击/滑动坐标并运行 parity，
  之后再处理 sortie 子页面。

## 2026-09-09 Stage 2 Navigation Review Round 1

- 已读取导航图、注册表、导航服务和全部页面回退入口，确认普通/决战/活动准备页
  不允许共享无来源回退边。
- 已记录选船页缺少独立 `go_back`、决战/活动准备页继承普通地图回退的兼容风险；
  按任务书要求暂不修改导航行为。
- 下一步核对导航栈的页面字符串/枚举契约和测试覆盖，完成 2.2 评审报告。

## 2026-09-09 Stage 2 Navigation Review Round 2

- 已验证导航栈页面字符串/枚举归一化和显式澡堂路线；navigation compileall、契约
  smoke 通过。
- 导航专项 `38 passed`、`3 failed`；失败均为既有架构测试与当前来源区分设计冲突，
  已记录在 findings，不回退现有实现。
- 下一步生成 2.2 导航兼容性评审报告并更新任务书；仍不新增模式无关导航边。

## 2026-09-09 Stage 2 Coordinate Format Batch

- 完成 `battle_preparation`、任务、战役和演习页面实际 click/swipe 坐标的四位化；
  旧校准像素 parity 通过，目标 compileall、pre-commit 和 diff check 通过。
- ROI、OCR 参数和像素签名未混入点击坐标治理；决战常量剩余值待视觉专项按类型处理。
- 下一步回到 Controller 函数分区，治理 home/sidebar/sortie 的可安全排序项。

## 2026-09-09 Stage 2 Controller Governance Batch C

- 完成 `DetectionMixin` 和 `repair_action.py` 的函数顺序治理，编队/战役/演习回归
  `169 passed`，目标 compileall、pre-commit 和 diff check 通过。
- 已保留 OCR 私有 API、上下文优先级、选船算法和浴室页面不变；下一批继续处理
  sidebar/home/sortie 的结构问题。

## 2026-09-09 Stage 2 Review Complete for 2.1 and 2.2

- 2.1/2.2 的结构治理和导航评审已完成；报告写入
  `meta/[报告]ui-controller导航兼容性评审报告.md`。
- 2.1 修复了非 OCR 私有模块导入、页面顺序、主要坐标格式和任务页状态入口；
  2.2 仅记录多来源回退风险，没有改变导航图行为。
- 下一步重读任务书后进入 2.3 OCR/ROI 与上下文所有权治理。

## 2026-09-09 Stage 2 OCR/ROI Audit

- 已完成 Controller 中 ROI/OCR 混用点、recognition 模块、通用视觉能力和 OCR 创建
  入口的审计；确认 common.vision 已有足够的无业务语义能力。
- 已确认选船/准备页 OCR 与页面算法耦合、BathPage 隐式创建 OCR、多个消费者调用
  OCR 私有函数，均按既有 TODO 留存，不迁移算法、不创建第二套 OCR 状态源。
- 下一步以模块导入方式修正 shared 选船、准备页检测和任务 OCR 的私有函数引用，
  再运行 OCR/ROI 相关 focused 回归并更新 TODO。

## 2026-09-09 Stage 2 Complete

- 已完成 2.1 Controller 规范治理、2.2 导航兼容性评审、2.3 OCR/ROI/上下文审计及
  阶段二复核，任务书状态已同步。
- 最终视觉/结构回归：UI 与视觉 `483 passed`；导航专项 `38 passed`、`3 failed`
  的旧架构断言已记录；compileall、目标 pre-commit、导入 smoke、坐标 parity 和
  `git diff --check` 通过。
- 未决问题全部留在上下文/OCR TODO，下一步重读任务书进入阶段三 ShiinaKuroko
  最近两日 commit 台账，不直接 merge/cherry-pick。

## 2026-09-09 Stage 3 Porting Audit Round 1

- 已建立并重读 ShiinaKuroko 最近两日 commit 台账，完成时间线和提交类型分类。
- 初步确认解析器兼容和模式澡堂导航在目标架构已有对应实现；维修终止、完整战果
  默认值、地图 OCR 导航和决战等待仍需逐文件核对。
- 调试工具包/二进制资源默认排除，地图压力测试只做场景评估；没有执行合并或
  cherry-pick。

## 2026-09-09 Stage 3 02ce4ed Baseline

- 已重读阶段三任务书、UI Controller 规范、导航规范和功能移植台账。
- `02ce4ed` 的目标映射确定为 `business/combat/plan.py`、
  `application/combat/engine/state.py` 及 `testing/combat/test_combat.py`；没有复制旧
  `autowsgr/combat` 模块，也没有修改 `bath_page`。
- 修复前复现：空 `CombatPlan` 的 `collect_result_info` 为 `False`，默认 MAP 状态图的
  `RESULT` 不进入 `EXP_SETTLEMENT`，与源提交要求不符。
- 下一步：手工移植默认值和测试断言，完成 focused pytest、compileall、import smoke、
  目标 pre-commit 和 `git diff --check` 后再回写台账并重读任务书。

## 2026-09-09 Stage 3 02ce4ed Complete

- 已将源提交语义移植到 `business/combat/plan.py` 和
  `application/combat/engine/state.py`；空计划默认完整采集，显式 `False` 仍保留快速
  穿行兼容路径。
- 测试断言同步到当前架构，`testing/combat/test_combat.py` 与
  `testing/combat/test_result_dismiss_unit.py` 共 `145 passed`；compileall、import smoke、
  scoped pre-commit 和 `git diff --check` 通过。
- 台账已标记 `02ce4ed` 已移植；下一项为 `9b000b4` 的任务级维修处理核对。

## 2026-09-09 Stage 3 9b000b4 Complete

- 已把 `repair_method` 从 API 请求到 `CombatPlan`、普通/活动运行器接通：`quick` 显式
  覆盖全局手动配置，`bath` 通过专用导航派修并等待目标舰船恢复，未声明时保留旧的
  `repair_manually` 兼容语义。
- 已将 `TaskStatus.REPAIRING` 接入任务占用、停止、进度和 WebSocket 更新；活动出征准备页
  通过 `BATTLE_PREP -> EVENT_MAP` 专用边返回后再进入澡堂，清理原活动 TODO。
- 相关 focused 回归 `177 passed`；compileall、import smoke、scoped pre-commit 和
  `git diff --check` 通过。首轮 `PLR0912` 和测试替身契约错误已记录在 task_plan Errors。
- 台账已标记 `9b000b4` 已移植；下一步重读任务书后核对 `1d7fca7` 地图固定 OCR 槽位。

## 2026-09-09 Stage 3 1d7fca7 Complete

- 已将普通出征章节导航从高亮条推算/抖动点击改为固定五槽位 OCR：槽位识别、章节标签
  解析和二值化复识别位于 `battle_page/recognition.py`，槽位选择位于 `data.py`，
  页面控制器只负责读取和点击。
- 已保留 `read_selected_chapter_y` 供现有 E2E 诊断使用，删除不再被生产调用的旧
  `click_chapter`，并将 `tools/check_sortie_api.py` 更新为 `click_chapter_slot`。
- 地图 focused 回归 `28 passed`；`tools/check_sortie_api.py`、compileall、import smoke、
  scoped pre-commit 和 `git diff --check` 通过。
- 台账已标记 `1d7fca7` 已移植；下一步重读任务书后核对 `0577f15` 决战浮层等待。

## 2026-09-09 Stage 3 0577f15 Complete

- 已在 `business/combat/decisive/handlers.py` 的进入地图状态中加入 2 秒稳定等待，
  防止首帧地图/overlay 识别抢在进图动画完成前执行；没有复制旧处理器或新增等待状态。
- 决战 focused 回归 `4 passed`，compileall、import smoke、目标 pre-commit 和
  `git diff --check` 通过；首轮 Ruff 自动修正已记录在 task_plan Errors。
- 阶段三来源逐项处理完成：`02ce4ed`、`9b000b4`、`1d7fca7`、`0577f15` 已移植，
  `e6d9fee`、`450c88a`、`7443018`、`c5a464c` 已核对，其他提交按台账排除。
- 下一步：重读任务书，做阶段三总复核并只读盘点决战 debug worktree。

## 2026-09-09 Stage 4 Decisive Debug Read-only Audit Started

- 已重读阶段四任务书和两份 UI/导航规范。
- 目标仅为只读检查 `AutoWSGR/.worktrees/20260907-autowsgr-decisive-debug-6e3a`，
  产出参考移植计划；不在该 worktree 或当前代码中自动移植决战升级。

## 2026-09-09 Stage 4 Decisive Debug Audit Complete

- 只读确认参考 worktree 分支为 `codex/20260907-autowsgr-decisive-debug-6e3a`、HEAD
  `9596446`，工作区仍有未提交的决战入口/浮层/准备页/稳定性调整和未跟踪本地配置、
  稳定性脚本；未修改该 worktree。
- 已盘点已提交的 `7bd0ece` 正向识别门禁、`c55f994` 准备页标题与地图识别修正、
  `9596446` 18 份 EX 节点图/MapData/分支卡片 ROI，以及当前未提交的 staged entry
  polling、reset/fleet 标题门禁和稳定性恢复尝试。
- 已与目标 `decisive_page`、`business.combat.decisive`、`common.system` 和现有地图资源
  对照，确认后续必须按资源契约 → 页面识别 → 状态机 → API/实机验证顺序执行；分支节点
  ID、0577 的 2 秒等待、旧 `enemy_spec.yaml` 删除和新模板纳入均需要单独确认。
- 已产出 `meta/[计划]决战流程升级移植参考计划.md`；阶段四只读任务完成，不执行代码移植。

## 2026-09-09 Task Complete

- 阶段一至阶段四任务书状态、`task_plan.md`、`findings.md`、`progress.md`、台账、阶段
  报告和决战参考计划已同步；主任务状态标记为 `done`。
- 最终验证：阶段三聚合 focused `408 passed`；全量 `compileall`、修正后的 import smoke、
  目标文件 scoped pre-commit 和 `git diff --check` 通过。
- 当前 worktree 仍保留用户已有的大量未提交/已暂存架构迁移改动；本任务没有执行提交、
  合并、cherry-pick、reset、stash、清理或远程操作。
