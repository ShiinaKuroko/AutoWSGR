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

- User selected `controller/main_page` as the actual home page and requested the
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
- Moved `controller/main_page/` to `controller/home_page/` and renamed
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
