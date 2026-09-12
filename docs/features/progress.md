# Progress Log

## Session: 2026-08-28

### Phase 1: Discovery
- **Status:** in_progress
- **Started:** 2026-08-28
- Actions taken:
  - Loaded the required Ponytail and persistent-planning instructions.
  - Ran the planning-session recovery check.
  - Identified the backend and GUI repositories.
  - Began reviewing local repository constraints.
  - Confirmed that cross-boundary implementation requires a user-confirmed plan.
  - Checked both repository worktrees and preserved the existing backend `.dbg/` directory.
  - Identified the GUI architecture and verification routes relevant to logging and filesystem configuration.
  - Resumed from the persistent plan and re-read the current task state.
  - Located the backend emission, backend ship-drop matcher, GUI statistics parser, and current GUI log-directory entry points.
  - Confirmed that ship-drop messages remain in both the backend statistics whitelist and GUI parser contract.
  - Identified a candidate initialization-order issue for the custom GUI log directory.
  - Found server sink registration and the GUI backend-log fan-out path; next trace is Electron transport into `onBackendLog`.
  - Distinguished Electron stdout forwarding from the backend WebSocket statistics-log route and narrowed the shared consumer to `SchedulerRuntimeTracker`.
  - Confirmed the `/ws/logs` callback chain reaches both `DailySortieStats` and the home-page `LogView`; began checking UI filtering and Electron file-write authorization.
  - Established the backend sink-removal root cause shared by home-page combat logs and ship statistics.
  - Established the UNC rejection and missing live Logger directory update that prevent the custom GUI log directory from working.
  - Completed discovery with three independent read-only traces; no backend or GUI source files were modified.

### Phase 2: Minimal Change Plan
- **Status:** complete
- Actions taken:
  - Prepared a two-batch plan: backend sink lifecycle/loop affinity and a dedicated configured GUI-log writer.
  - Received user confirmation to implement.

### Phase 3: Implementation
- **Status:** in_progress
- Actions taken:
  - Started independent backend and GUI implementation tracks in parallel.
  - Collected existing backend and GUI focused test entry points for final verification.
  - Backend focused sink tests passed in the implementation track.
  - GUI main-services test passed; one broader IPC command currently fails at a pre-existing updater assertion and the Electron-only settings test needs its package-script runner.
  - GUI `npm run test:settings` then failed at an existing log-root dirty-state assertion and its temporary userData cleanup was busy; dedicated configured-root service coverage remains the targeted validation.
  - Main-thread precheck verified updated callers and clean diffs in both repositories.
  - Main-thread backend verification passed: 10 focused pytest cases and Python compilation.
  - Main-thread GUI main-services/build and daily-sortie-stats checks passed.
  - Main-thread GUI build-contract check passed; final diff checks passed in both repositories.

### Phase 4: Verification
- **Status:** complete
- Results:
  - Backend focused sink and system-route tests: 10 passed.
  - Backend changed-module compilation: passed.
  - GUI main-services/build: passed.
  - GUI daily-sortie-stats: passed.
  - GUI build/output/renderer contracts: passed.
  - Both diffs: passed `git diff --check`.
  - GUI settings and broad main-IPC commands retain their separately documented unrelated failures.

### Phase 5: Delivery
- Packaging preflight started after the verified logging fixes were pushed.
- Phase 6 preflight collected current versions, release metadata, and the alpha builder output path; awaiting explicit version/channel confirmation.
- **Status:** complete
- Delivered the backend log-flow restoration and secure configured GUI-log writer.
  - Began requested commit/push handoff; both repositories are already on `ShiinaKuroko`, but fetch failed due to GitHub HTTPS connectivity.
  - Diagnosed the failed HTTPS transport and selected direct SSH-over-443 push without changing the configured origins.
  - Confirmed SSH-over-443 has no usable GitHub identity; proceeding with local commits only.
  - Created local commits `4a1809a` (backend) and `7f3c99c` (GUI), excluding the pre-existing backend `.dbg/` directory.
  - Attempted direct SSH-over-443 push for the backend; GitHub rejected the unavailable public key, so the GUI push was not repeated.
  - Retried after SSH configuration changed: backend push succeeded and remote SHA was verified; GUI push remains blocked by deploy-key scope.
- Files created/modified:
  - `task_plan.md` (created)
  - `findings.md` (created)
  - `progress.md` (created)

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Backend sink lifecycle | `pytest testing/server/test_ws_log_sink.py testing/server/test_system_routes.py -q` | Drop reaches WebSocket after logger reset | 10 passed | Pass |
| Backend syntax | `python -m py_compile` changed server modules | Valid Python | Passed | Pass |
| GUI main services | `npm run test:main-services` | Build and configured-root writer pass | Passed | Pass |
| Daily stats | `npm run test:daily-sortie-stats` | Ship-drop parsing remains valid | Passed | Pass |
| GUI build contracts | `npm run test:build` | Build, DOM, and architecture contracts pass | Passed | Pass |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| 2026-08-28 | UTF-8 output mojibake | 1 | Use explicit UTF-8 reads. |
| 2026-08-28 | Planning-file patch context mismatch | 1 | Re-read current text and used narrower patch anchors. |
| 2026-08-28 | Broad GUI search named nonexistent `test` and `tests` directories | 1 | Use known paths and package-script discovery instead. |
| 2026-08-28 | Repeated backend search named nonexistent `tests` directory | 2 | Stop using guessed test directories; inspect package configuration first. |
| 2026-08-28 | Backend runtime reproduction lost quoting in PowerShell | 1 | Use static call-order evidence; do not repeat the same shell form. |
| 2026-08-28 | GUI `test-main-ipc` updater assertion | 1 | Preserve unrelated updater behavior; report it separately. |
| 2026-08-28 | GUI settings test run with Node | 1 | Use Electron package script. |
| 2026-08-28 | GUI `test:settings` dirty-state assertion / EBUSY cleanup | 1 | Preserve unrelated behavior; report and use dedicated service coverage. |
| 2026-08-28 | Narrow Node IPC check quote loss | 2 | Stop retrying quoting variants; rely on existing focused coverage and static audit. |
| 2026-08-28 | GitHub fetch cannot connect to `github.com:443` | 1 | Inspect Git/proxy configuration and reachability before retrying. |
| 2026-08-28 | GitHub SSH-over-443 public-key authentication | 1 | Commit locally; await credentials or HTTPS recovery for push. |
| 2026-08-28 | Direct SSH-over-443 push rejected | 1 | Do not repeat for GUI; await GitHub credentials or HTTPS recovery. |
| 2026-08-28 | GUI deploy key lacks repository permission | 1 | Backend pushed; await GUI repository write permission or a personal SSH identity. |
| 2026-08-28 | Planning-file patch empty hunk | 1 | Reapplied only non-empty updates. |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 1: Discovery |
| Where am I going? | Trace log flow, plan minimal fixes, implement after required confirmation, verify. |
| What's the goal? | Restore combat-drop logs/statistics and configured GUI log storage. |
| What have I learned? | See `findings.md`. |
| What have I done? | See above. |

## Phase 6: GitHub Packaging
- Found the existing failed run's only failed step: `Verify pinned backend`.
- Updated the stale Alpha backend pin to the current pushed backend commit and committed `f92078a`.
- Fetched, pushed, and manually dispatched the repository's existing `release.yml` workflow.
- Run `33105288742` passed; Release `v2.1.1-alpha.6` assets were refreshed successfully.

## 2026-08-29 Sakuya Architecture Audit
- Created isolated task worktrees from local backend `ShiinaSakuya@8745604`:
  `codex/20260829-sakuya-architecture-audit-6b2e`.
- Ran the Sakuya WIP full suite with an isolated basetemp: `1015 passed in 14.38s`.
- Verified the central Processor is not referenced by production server routes,
  scheduler, or CLI; `server/api` and `server/console` contain only package
  docstrings.
- Reproduced direct-import circular failures for
  `autowsgr.infra.base.ui.pages.map` and `mission_page`.
- Reproduced removed public imports for `autowsgr.ops.exercise`,
  `autowsgr.ops.expedition`, and `autowsgr.ops.reward`.
- Reproduced priority inversion: Processor pops priority `200` before `0`, while
  `daily_plan` documents `0` as the most urgent priority.
- No production code was changed; audit findings and the proposed safe restart
  sequence are the current deliverable.
- Additional contract audit: Sakuya hard-codes chapter selection at `0.556` and
  drops the Kuroko dynamic sidebar-highlight scan; direct imports of new map and
  mission packages fail because the new UI layer imports old `autowsgr.ui`.
- User approved replacement-mode Sakuya workflow and branch-local process gates;
  updated the architecture worktree's `AGENTS.md` only. The file is explicitly
  excluded from all future code transfers to other branches.

### Baseline Sync Checkpoint
- Confirmed current local `ShiinaSakuya` at `16349d20` after the Kuroko merge.
- Merged it into `codex/20260829-sakuya-architecture-audit-6b2e` as `8bf5d168`.
- Verified the audit worktree is clean, `git diff --check` passes, all non-
  `AGENTS.md` paths match `ShiinaSakuya`, and the branch-local `AGENTS.md`
  remains preserved.

### Macro Architecture Review Checkpoint
- Reviewed the target `server -> dispatch -> business/navigation -> infra`
  topology for reasonableness, maintainability, simplicity, and clarity.
- Conclusion: the macro design passes without adding layers; five red lines must
  close before implementation (single production entry, single task-state owner,
  confirmed pause/cancel handshake, single runtime/lease owner, and no new-code
  dependency on legacy `ui/ops`).
- Clarified that `CombatEngine` is a domain service below business, while
  `RuntimeSession` is a runtime capability boundary rather than a task-state
  container. No production code changed.

### Shared Navigator Review Checkpoint
- Evaluated the case where both dispatch and business need navigation.
- Proposed one shared semantic `Navigator` as a peer sublayer beside business
  orchestration inside the application layer; do not create separate dispatch and
  business navigators or a new top-level layer.
- Split ownership: Processor decides when/why and target task anchor; Business
  declares internal semantic anchors; Navigator computes and verifies the safe
  route; infra implements page/vision/device mechanics.
- No production code changed; the proposal is recorded as pending user approval.

### Task-Handoff Ownership Clarification
- Refined the previous proposal: task-to-task handoff policy belongs to
  `dispatch/Processor` (whether to hand off, target anchor, context reuse, and
  when the next task may start).
- Shared `Navigator` owns only execution of the safe route from the current
  anchor to the selected target and its stability confirmation.
- Business use cases declare their own entry/safe/terminal anchors and report
  actual terminal state; they do not choose the next task or the A-to-B policy.
- A future `HandoffPolicy/Coordinator`, if needed, remains inside dispatch and
  must call the same Navigator. No production code changed.

### Business-Domain Boundary Review
- Confirmed the architectural distinction: Business does not own task-to-task
  navigation or route calculation. A use case may declare an anchor required by
  its next internal step, while the shared Navigator owns path execution and
  verification.
- Reviewed the proposed combat/life split against current Sakuya code. The
  confirmed code-domain names are `combat` and `homeport`: the latter is clearer
  than `logistics` for destroy, retrofit, construction, repair, mission, and
  backyard operations without conflicting with technical ports.
- Recorded that normal/event sorties use one executor; exercise, campaign, and
  decisive remain separate; fleet selection reuses a small shared policy and
  infra capability; quick repair stays inside combat preparation while bath
  repair is an independent homeport task.
- No production code, GUI code, API contract, or test was changed.

### Business Package Organization Confirmation
- User confirmed package-oriented business organization: each independently
  executable use case has its own package and a single `executor.py` entry;
  related rules, input specification, checkpoints, and local state live beside
  it when they have a real separate responsibility.
- Shared capabilities are explicit exceptions: `navigation` exposes a
  `Navigator`, combat engine exposes engine APIs, and fleet policy remains pure
  rule data. None receives a fake `Executor` merely to fit the package shape.
- `__init__.py` remains export-only. It does not own execution, registration,
  state, or compatibility behavior. No production code changed.

### Infrastructure Inventory Checkpoint
- Began the next architecture discussion phase in the isolated Sakuya audit
  worktree. No GUI, API contract, production code, test, merge, or push change
  was made.
- Confirmed the physical infrastructure is split across `infra`, `emulator`,
  `vision`, `ui`, `data`, and `GameContext`; the existing `infra` directory is
  not yet a coherent final boundary.
- Identified duplicate navigation and stop-state ownership as migration targets.
  The next decision is the target infrastructure boundary, not a premature move
  of code.
- User challenged the `port` code-domain name. It is now confirmed as rejected;
  `homeport` is the final code-domain name.

### 2026-08-30 Architecture Discussion Checkpoint
- User confirmed `homeport` as the 港区 business-domain code name.
- A broad documentation patch failed before applying because one stale phrase did
  not match its expected context. The follow-up uses narrow, exact patches; no
  production or GUI file was touched.
- A follow-on historical-block patch also failed before applying because its list
  prefix differed from the expected context. After reading the exact lines, a
  single-context replacement completed the correction; do not retry broad
  multi-file documentation patches in this task.
- Recorded the next proposed baseline: keep the existing emulator boundary;
  separate CV2 positioning from FastOCR text reading; defer YOLO; place UI
  calibration in read-only resources; and split the current context ownership by
  lifecycle instead of hanging a new mutable context from Processor.

### Infrastructure Dependency Checkpoint
- Verified that `AndroidController` and the core vision API have useful existing
  low-level boundaries and do not need speculative replacement wrappers.
- Found two additional misplaced process-global owners: the page registry is
  populated by UI import side effects, and the shared emulator lease lives in
  `server`. These are design inputs for `RuntimeSession` and `Navigator`, not
  a reason to move files before their contracts are agreed.

### 2026-08-30 Context and Calibration Checkpoint
- User confirmed `homeport`; this phase focused on central coordinate access and
  the meaning of task context.
- Recorded the preferred dotted access shape as a typed `UIProfile` namespace,
  while keeping business executors dependent on semantic page capabilities rather
  than coordinates themselves.
- Defined the ownership split: Processor/TaskInstance for task lifecycle,
  ExecutionAttempt for local run state, RuntimeSession for reusable runtime
  capabilities, Navigator for navigation state, and GameStateStore for observed
  cross-task game facts.
- Defined the only two upward distribution paths: task events to Processor and
  typed observations to GameStateStore. Raw CV2/OCR results stay local unless a
  checkpoint or diagnostic evidence explicitly requires retention.

### 2026-08-30 Entry-to-Processor Discussion Preparation
- Re-read the isolated worktree status, architecture minutes, and applicable
  repository instructions.
- Traced current HTTP task/system routes, `TaskManager`, `TaskScheduler`, the
  dispatch `Processor`, registry, and launcher entry points.
- Confirmed no production or GUI code changes are being made in this discussion
  phase; the next action is to settle the top-level command and runtime-host
  boundary before documenting the final proposal.

### 2026-08-30 Control Plane Design Inventory
- User narrowed public entry points to CLI and GUI HTTP, with a compatibility
  translation stage before Processor.
- Inspected existing entry scripts, legacy plan resolution, plan YAML shapes,
  `auto_daily`, and package configuration. Recorded the proposed control-plane
  vocabulary, YAML migration boundary, compatibility rules, and open business
  decisions in the architecture minutes.
- No backend or GUI production code, public API, test, merge, or push changed.

### 2026-08-30 One-Shot Task Boundary Discussion
- User confirmed that YAML drives GUI tasks and that the backend's minimal unit
  is one finite task execution; timers/idle behavior submit additional tasks.
- Reframed RuntimeHost/RuntimeControl/TaskCommand in business terms (system
  switch, task order, and dispatch desk) and recorded the minimal validation,
  compatibility, queue-duplication, and GUI status rules.
- No backend or GUI production code, public contract, test, merge, or push
  changed.

### 2026-08-30 Entry Model Clarification
- User confirmed the public entry shape as CLI/GUI HTTP followed by command
  recognition and compatibility conversion, then direct submission to Processor.
- Clarified that scheduling/idle triggers may be GUI-side or backend-side and
  always submit finite one-shot tasks; `RuntimeHost` terminology is explanatory,
  not a new user-facing layer.
- No backend or GUI production code, public contract, test, merge, or push
  changed.

### 2026-08-30 Entry Contract Corrections
- Applied the user's corrections to execution count, YAML compatibility, local
  duplicate-submission scope, GUI priority orchestration, forced backend
  shutdown, and the CLI live-status TODO.
- Recorded the three-way pause/stop/interrupt semantics and the remaining
  macro questions around repeat batches, task-kind identification, queue
  authority, and GUI/backend lifecycle.
- No backend or GUI production code, public contract, test, merge, or push
  changed.

### 2026-08-30 Macro Decision Queue
- Consolidated the user's latest corrections and added the remaining macro
  decisions in priority order: repeat-batch visibility, task-type identification
  without changing YAML, repeat failure/stop semantics, queue authority, forced
  GUI/backend process ownership, normal shutdown queue handling, and startup
  recovery from an unknown emulator page.
- No backend or GUI production code, public contract, test, merge, or push
  changed.

### 2026-08-30 Final Business Decisions and Implementation Start
- User closed the remaining macro decisions: GUI owns the submitted-count
  denominator and backend returns completed `count`; task type is read from the
  YAML generated by GUI; soft retry may escalate to hard retry/SL reinitialization;
  CLI stops on failure while GUI retains remaining count; hang-up is a trigger that
  submits finite tasks; GUI and backend queues are separate during the current
  integration stage and `extre` carries insertion intent; forced GUI/CLI close is
  process termination; restart always reinitializes and reconciles to home.
- Architecture discussion is complete enough to implement. The first slice is
  exercise, with no GUI source changes and no new dependency.
- Production implementation begins in the isolated AutoWSGR worktree. No code
  changes have been made yet in this checkpoint.

### 2026-08-30 E2E Hardening Start

### 2026-08-30 Processor Verification Start
- Re-read the implementation diff and all direct Processor/route callers.
- Re-ran the focused server, schema, and E2E tests with the repository
  `.venv` and writable `--basetemp=.pytest-tmp-sakuya`: `125 passed`.
- Found bounded-priority and input-admission issues not covered by existing
  tests; these are the next implementation checks.
- Implementation batch 1 is limited to the reusable `tools/e2e` lifecycle:
  prepare must perform the same initialization contract, abnormal game exits
  must be reinitialized, and every case must attempt a final home-page cleanup
  and device disconnect before reporting its verdict.
- Existing `tools/debug_screenshot.py` and `tools/ocr_crop_tool.py` are the
  approved debug tooling; no replacement OCR or screenshot package is needed.
- Implemented the first E2E lifecycle pass in `tools/e2e/framework.py` and
  `tools/e2e/run.py`: normal cases initialize through `business.system.initialize`,
  action boundaries detect/recover an exited game, and finalization attempts
  home-page cleanup plus device disconnect even for raised exits.
- Added `testing/tools/test_e2e_framework.py` for the recovery/cleanup contract.
- System-level `python -m pytest` and `ruff` were unavailable; repository
  environment verification is still pending.

### 2026-08-30 Processor Verification Continuation
- Fixed the new Processor test's `MagicMock` import and bounded max-priority
  interruption. `extre` now wins equal-priority queue ties without exposing a
  priority above 10.
- Flattened Processor list results at the HTTP adapter so `TaskResult.details`
  remains the existing GUI-compatible `RoundResult[]`; inner failures now make
  the task outcome fail.
- Added strict mapping admission for `Request.params`, safe CLI YAML-error
  reporting, YAML route admission tests, and E2E cleanup coverage through the
  public launcher disconnect method.
- Focused validation: `48 passed`; compileall and `git diff --check` passed.
- Full validation: `1050 passed, 3 failed`; all failures are existing repair
  tests importing the removed `autowsgr.ops.repair` module. This needs a
  separate compatibility decision and is outside the current exercise slice.

### 2026-08-30 Exercise Slice Final Verification
- Repaired the E2E `try/except/else` syntax regression and completed the
  remaining Ruff import, return-path, and formatting fixes.
- YAML syntax errors now become admission `ValueError`s (and therefore HTTP
  `422`), and the exercise preparation-page stop path uses its safe back-out
  route before returning home.
- Final focused validation: `63 passed` for dispatch, task routes/system/ws,
  and E2E lifecycle tests.
- Final full validation: `1054 passed, 3 failed`; the same three existing
  `testing/ops/test_repair_unit.py` cases fail to import the removed
  `autowsgr.ops.repair` module.
- Final static validation: changed Python files pass Ruff check/format,
  `compileall`, and `git diff --check`.
- Pytest basetemp directories were moved out of the repository into the local
  system temp directory; no GUI files or other worktrees were changed.
- The isolated child worktree checkpoint is `ccc0240`; no merge or push was
  performed.

## 2026-08-30 Complete Exercise Migration

- Created isolated meta/backend worktrees on branch
  `codex/20260830-sakuya-exercise-migration-8d3f`, based on the prior Sakuya
  exercise slice (`ccc0240` backend, `2fcf991` meta).
- User requested static verification before any real-device E2E; no device
  test has been started in this task.

### Static Inventory Complete

- Confirmed reusable pieces: `CombatEngine` already handles exercise result
  settlement and returns to the exercise page; `combat/fleet.py` already has
  immutable fleet rules; the tested fleet-change algorithm is the normal-sortie
  implementation.
- Confirmed migration gap: `business/combat/exercise.py` is still a flat
  compatibility-heavy executor and directly imports legacy UI/ops; its YAML
  validator only permits `fleet_id`, `rival`, and `rivals_limit`.
- Confirmed deterministic import failure: importing
  `autowsgr.infra.base.ui.pages.map` before `autowsgr.ui` raises a circular
  import through `ui.utils` and the `ui.map` shim. This is the first static fix
  before any new exercise executor import is enabled.

### Infra Boundary Pass

- Moved the battle-preparation page, fleet-change mixins, chooser, ship-list
  OCR helper, and navigation interaction helper into `infra/base/ui`.
- Added legacy module aliases under `autowsgr/ui` so existing normal/decisive
  consumers and their patch targets continue to resolve to the moved modules.
- Updated map panels, combat handlers/actions, and quick-repair imports to the
  infra paths. Direct imports of map, battle preparation, and exercise now pass.
- Deferred event-map template loading in `combat/recognizer.py` to remove the
  remaining import cycle; no event behavior was changed.

### Static Boundary Regression

- Existing moved-surface regression passed: `337 passed` across battle
  preparation, chooser, ship-list, navigation, normal-fight, and combat tests.
- No real-device E2E has been run; the five-attempt budget remains untouched.

### Exercise Definition and Control Checkpoint Pass

- Added `business/combat/exercise/spec.py` and the team-2 fixture to normalize
  `fleet_presets`/`fleet_rules`, primary/fallback rules, and exercise defaults.
- The executor now consumes the normalized fleet selection, runs repair/supply
  preparation, emits selection/formation/battle checkpoints, and keeps cleanup
  errors from replacing the original failure.
- Added no-device executor tests; current exercise-business focus is `6 passed`.
- Changed Processor's priority ordering to the minutes' small-number-high rule
  and added safe-checkpoint handoff detection. Existing Processor focus is
  `17 passed`.

### Full Static Gate (intermediate)

- First full pytest run after migration: `1064 passed, 4 failed`.
- Three failures are the pre-existing missing `autowsgr.ops.repair` module.
- One failure was caused by the new task-specific OCR candidate keyword changing
  an exact mocked call; the implementation now keeps the old call shape for
  built-in names and only passes the keyword for unknown task names.
- `compileall` and direct import checks pass. Ruff is available through `uvx`,
  but the repository has a broad pre-existing lint backlog; changed files will
  be checked separately before the final gate.

### Handoff/E2E Preparation

- Added a compatibility alias for `autowsgr.ops.repair`; its 10 focused tests
  pass and the new business implementation remains the single source.
- Updated the exercise E2E case to use the checked-in team-2 YAML fixture by
  default, support either expedition or mission/reward checks, and cover the
  five user-specified relay breakpoints. No device run has started.

### Static Gate Refresh

- Full repository pytest: `1069 passed`.
- Targeted Ruff check: passed for new exercise/dispatch/route/fleet/E2E files;
  remaining findings are inherited from the moved page modules and unrelated
  repository debt.
- Ruff format check/fix applied only to the touched combat handler and E2E case.
- Real-device attempt counter remains `0/5`.

### Read-only Device Preflight

- ADB CLI is not on PATH, but the repository's `adbutils` can see
  `emulator-5554` in `device` state.
- The game process `com.huanmeng.zhanjian2` is running; a 1280x720 screenshot
  was saved outside the repository and recognized as `PageName.HOME`.
- No device input was sent; real-device attempts remain `0/5`.

### Real E2E Budget Plan

- Attempt 1 (next): team 2, same requested fleet rules, one rival, no
  interruption; validate the complete primary path and strict OCR.
- Attempt 2: team 2 again, one rival, no interruption; validate recognition of
  the already-satisfied primary configuration without unnecessary replacement.
- Attempt 3: switch to a different fleet, one rival; validate real replacement
  and ordering.
- Attempt 4: one safe breakpoint with `expedition_check` insertion.
- Attempt 5: one safe breakpoint with `reward_check` or the full relay, chosen
  only after reviewing the first four results.

### Real Attempt 1/5

- Command: `tools/e2e/run.py --with-ocr --fast-ocr exercise --with-init
  --fleet-id 2 --rivals-limit 1`.
- Result: failed during fleet preparation before battle. U-177, 阿尔戈、卡萨比
  安卡、U-103 were selected; S-198/S189 and the final fallback were not found.
- Cleanup was interrupted after repeated false `活动页面` recognition; a final
  initialization restored the emulator to the home page. Logs are under
  `logs/e2e_tools/exercise/20260830_061859/`.
- Budget changed to `1/5`; static fixes are required before attempt 2.

### Static Follow-up After Attempt 1

- Read-only screenshot/template analysis reproduced the false activity-page
  classification: the full-screen event `出击准备` template matches the
  preparation-page title at the upper left.
- The next code batch is deliberately limited to the event matcher search
  region, preparation-page cleanup, and accurate terminal OCR failure logs,
  each with no-device regression coverage. No additional device input has been
  sent.

### Static Follow-up Implementation

- Constrained the event overlay button matcher to its lower-right ROI; the
  captured preparation-page screenshot now returns no activity-page match.
- Added explicit preparation-state tracking and cleanup through
  `BattlePreparationPage.go_back()` before shared home navigation.
- Moved the exercise “进入战斗” log after the actual start click and changed
  terminal OCR exhaustion logging to report only unmatched or unverified slots,
  including type and level requirements.
- Added focused regressions; exercise, preparation, and event tests now pass
  (`145` preparation/exercise tests and `14` event tests).

### Static Gate Checkpoint

- Full repository pytest: `1073 passed`.
- Full compileall and direct imports of the moved map, preparation, and
  exercise modules passed.
- Ruff check/format passed for all new and directly changed exercise,
  dispatch, server, event, and test files; inherited moved-page findings remain
  explicitly isolated in the audit record.
- `git diff --check` passed. Backend checkpoint commit: `3ccd887`.
- No additional real-device input was sent after attempt 1.

### Account-Valid Smoke Preparation

- Kept `testing/fixtures/exercise_team2.yaml` unchanged as the requested
  six-slot strict-input case.
- Created ignored one-off `.tmp/e2e/exercise_account_valid.yaml` with the four
  ships confirmed selectable in attempt 1, so remaining device attempts can
  exercise navigation and battle instead of repeating a known account-data
  failure.
- Parsed the override through the same `Request.from_yaml` admission path and
  reran dispatch/task-route focus (`60 passed`). A read-only device preflight
  still reports the game at `主页面`; no device input was sent.

### Real E2E Attempt 2/5 (account-valid smoke, passed)

- Command: `tools/e2e/run.py --with-ocr --fast-ocr exercise --yaml
  .tmp/e2e/exercise_account_valid.yaml --rivals-limit 1`.
- The framework initialized from `主页面`; the processor routed through the
  exercise panel, selected opponent 1, and entered battle preparation.
- FastOCR/DLL recognized the four account-valid ships already in fleet 2; the
  fleet validator passed without opening any replacement flow. Supply,
  single-column formation, night battle, result settlement, and return to the
  exercise panel all completed.
- Processor result: one completed exercise round, `rival_done` count `1`;
  E2E execution-flow, count, terminal-home, cleanup, and disconnect checks all
  passed. Runtime was about 55 seconds.
- Logs: `logs/e2e_tools/exercise/20260830_071041/`. Attempt budget is now
  `2/5` (three remaining).

### Attempt 3 Preparation

- Created ignored `.tmp/e2e/exercise_fleet1.yaml`, switching the target to
  fleet 1 while retaining the four ships confirmed available in the account.
- The override parses through `Request.from_yaml`; exercise/preparation focus
  remains green (`145` passed) and targeted Ruff remains clean.
- Planned command omits `--with-init` and uses `--rivals-limit 1`; this attempt
  is reserved for actual fleet switching/replacement, not the unavailable
  six-slot fixture.

### Real E2E Attempt 3/5 (fleet switch, deterministic account constraint)

- Command: `tools/e2e/run.py --with-ocr --fast-ocr exercise --yaml
  .tmp/e2e/exercise_fleet1.yaml --rivals-limit 1`.
- Initialization, map/演习 navigation, opponent selection, and fleet-1 entry
  succeeded. The fleet algorithm found all four requested names in the ship
  list and issued replacement/removal clicks, but the game left fleet 1
  unchanged because those ships were already assigned to fleet 2.
- Final OCR correctly rejected the unchanged fleet after the bounded local
  retries; Processor soft/hard retries then produced a terminal `failed`
  outcome. No battle was started. Cleanup returned from the map to `主页面`
  successfully, with no activity-page false match or cleanup loop.
- Runtime was about 5.5 minutes due the configured retry budget. Attempt budget
  is now `3/5`; do not repeat cross-fleet assignment of fleet-2 ships.

### Real E2E Attempt 4/5 (panel handoff + expedition check, passed)

- Command: `tools/e2e/run.py --with-ocr --fast-ocr exercise --yaml
  .tmp/e2e/exercise_account_valid.yaml --rivals-limit 1 --pause-at
  panel_ready --check expedition_check`.
- At `panel_ready`, the processor paused the exercise and inserted the higher
  priority expedition check. The real account had four completed expeditions;
  all four were collected and the check returned to `主页面`.
- The exercise resumed from its preserved request, selected opponent 2,
  reused the valid fleet 2 without replacement, completed formation, night
  battle, settlement, and `rival_done` count `1`.
- Execution-flow, pause-home anchor, inserted-task count, result count, final
  home, cleanup, and disconnect checks all passed. Runtime was about 120
  seconds. Attempt budget is now `4/5` (one remaining).

### Attempt 5 Preparation

- Static handoff focus passed (`62` tests) for Processor, exercise, task-route,
  E2E lifecycle, and import/compile checks.
- One initial static command named a nonexistent `testing/business/logistics`
  directory; it was corrected by inspecting `testing/business` and was not
  repeated. The corrected command passed.
- Final device command is reserved for `before_start` with `reward_check` and
  the account-valid fleet-2 YAML; no device input has been sent for attempt 5.

### Real E2E Attempt 5/5 (preparation handoff + reward check, passed)

- Command: `tools/e2e/run.py --with-ocr --fast-ocr exercise --yaml
  .tmp/e2e/exercise_account_valid.yaml --rivals-limit 1 --pause-at
  before_start --check reward_check`.
- The exercise reached `before_start`, returned safely from preparation to the
  map/home path, and yielded to the higher-priority reward check. The real
  account had a pending task reward; `reward_check` collected it and returned
  to `主页面`.
- The exercise resumed, selected opponent 3, reused the valid fleet 2, and
  completed formation, night battle, settlement, and `rival_done` count `1`.
- Execution-flow, pause-home anchor, reward-task count, result count, final
  home, cleanup, and disconnect checks all passed. Runtime was about 77
  seconds. Attempt budget is now exhausted at `5/5`.

### Migration Report Checkpoint

- All five real-device attempts are recorded in `exercise-migration-report.md`.
- No GUI source files or GUI visual/interaction code changed in this branch.
- Remaining work is documentation and final static/diff verification only; no
  further device input is permitted for this task.

### Final Verification and Delivery Record

- Final code remained unchanged after the static checkpoint and all five E2E
  runs; backend worktree is clean at `3ccd887`.
- Final compileall/direct-import checks and targeted Ruff check/format passed;
  the full pytest result remains `1073 passed`.
- The one broad Ruff run against moved legacy UI files still reports inherited
  complexity/style findings; these are listed in the report and were not
  broadened into this feature slice.
- Added `exercise-migration-report.md` with the complete migration, contract
  boundary, static, E2E, and residual-risk record. No GUI worktree was touched.

## 2026-08-30 Exercise Executor Boundary Cleanup

- Moved the legacy `ExerciseRunner`, `ExerciseOnceRunner`, and `run_exercise`
  wrappers from `autowsgr/business/combat/exercise/executor.py` to the new
  package-local `compat.py`; the executor now contains only the Sakuya task
  implementation and registration.
- Updated package exports and the feature document, and added a regression
  asserting that legacy entries stay outside the executor module.
- Focused validation: `96 passed`; compileall, Ruff check/format, import smoke,
  and `git diff --check` passed.
- Backend checkpoint: `5c220bf refactor(exercise): isolate legacy entry adapters`.
- Removed the remaining compatibility wording from the executor docstring so
  its limits describe task semantics rather than legacy callers.
- Backend documentation checkpoint: `f4e08c1 docs(exercise): clarify executor ownership`.

## 2026-08-30 Minimal Exercise Boundary Pass

- Removed the deferred `ExerciseRunner` / `ExerciseOnceRunner` /
  `run_exercise` compatibility layer and its package exports; old compatibility
  is intentionally deferred until a later integration slice.
- Moved the combat foundation used by the exercise path into
  `autowsgr/infra/base/combat/`: map pages and panels, battle preparation,
  fleet-change mixins, choose-ship, and ship-list recognition. Existing logic
  was moved and imports were updated; no duplicate implementation was added.
- Focused combat migration tests: `254 passed`; full pytest: `1073 passed`.
  Import/compile checks, Ruff import checks, and `git diff --check` passed.
- Backend checkpoints: `e26f91f` (remove compatibility) and `b18337d`
  (group combat foundations).
- Updated `exercise-migration-report.md` to the consolidated branch, the
  `infra/base/combat` layout, and the Processor-only exercise entry; report
  checkpoint: `cfdf528`.

## Session: 2026-08-30 Branch Consolidation

- Consolidated the architecture-audit and exercise-migration history into the
  single bound branch `codex/20260830-sakuya-exercise-consolidated-7a6c`.
- Fast-forwarded the backend result into `ShiinaSakuya` at `3ccd887`.
- Removed the old local A/B/C branch refs and their worktrees; no GUI source
  or Kuroko worktree was modified.
- Kept the remote architecture-audit ref untouched; remote cleanup requires a
  separate explicit request.

## Session: 2026-08-30 Agent Binding and IDE Mapping

- Bound Agent `01a0446f-5999-7bc2-aa74-fc1a2887a8a9` to the consolidated backend
  worktree and verified the binding with `agent_worktree_binding.py`.
- Verified `.idea/vcs.xml` already tracks both consolidated meta and backend
  worktree roots; no duplicate XML entry was added.
- The IDE file is ignored local state. Backend and meta working-tree diffs are
  empty; the binding/documentation diff is recorded in this commit.
- Corrected the ignored `.idea/vcs.xml` mappings to the actual worktree roots:
  `.../.worktrees/20260830-exercise-team-contract-4c71/meta` and
  `.../.worktrees/20260830-exercise-team-contract-4c71/AutoWSGR`.
  Diff record: both old `.../20260830-sakuya-exercise-consolidated-7a6c/...`
  mapping lines were replaced with the actual paths above.

## Session: 2026-08-31 Campaign Migration

- Confirmed the bound worktree and preserved the eight user-deleted feature
  documents plus all unrelated working-tree changes.
- Traced the Kuroko campaign chain and verified the new Processor route,
  registry entry, daily trigger, map panel, preparation page, and combat
  result conversion.
- Added the campaign business package:
  `autowsgr/business/combat/campaign/{spec,operations,executor}.py`.
- Moved campaign calibration data to common resources:
  `common/data/calibration/{coordinates/map.yaml,colors/campaign.yaml,ocr/campaign.yaml}`
  and exposed it through `common/calibration/map.py`.
- Replaced the server campaign runner loop with a `Request` submitted to
  `Processor`; the old `ops/campaign.py` is only a forwarding facade.
- Added campaign fleet-source admission checks and HTTP 422 coverage for an
  unknown direct campaign name.
- Focused campaign/dispatch/server tests: `67 passed`.
- Adjacent combat/map/preparation/scheduler/server tests: `415 passed`.
- Full repository pytest: `1094 passed in 12.30s`.
- Targeted pre-commit passed all hooks; compileall and `git diff --check`
  passed; `uv build` produced the 2.3.0 sdist and wheel successfully.
- Backend commit: `a1786f4` (`feat(campaign): migrate campaign execution to processor`).
- No campaign device E2E was run. An external edit appeared in
  `autowsgr/business/combat/exercise/executor.py` after the final status check;
  it remains unstaged and untouched.

## Session: 2026-08-31 Campaign Fleet Rules

- Reviewed the existing fleet-change chain and identified compaction and drag
  as campaign-specific incompatibilities.
- Added `application/ui/pages/battle_preparation/fleet_change/campaign.py`
  with a `CampaignFleetChangeMixin`; `BattlePreparationPage` selects it from
  the task type while delegating other task types to the existing Mixin.
- Added hard campaign type/count rules and current-fleet validation in
  `business/combat/campaign/spec.py` and campaign preparation operations.
- Updated campaign fleet policy and combat-domain documentation; no GUI source
  was modified.
- Updated the exercise test stub to assert the propagated `exercise` context.
- Campaign pytest: `22 passed`; exercise pytest: `13 passed`.
- Targeted Ruff, format, and pre-commit checks passed; no full pytest was run,
  per user instruction.
- Backend commit: `22e314e` (`feat(campaign): add fixed-slot fleet strategy`).
- User-deleted documents and the external unstaged
  `business/combat/exercise/executor.py` edit remain untouched.

## 2026-09-01 Campaign Contract Audit

- Re-read the bound repository rules, corrected campaign taskbook, architecture
  notes, current plan, and all campaign direct callers.
- Confirmed the backend worktree and immutable Agent binding remain unchanged.
- Audited `CampaignExecutor`, `CampaignOperations`, campaign fleet mixin,
  navigation graph/service, Processor handoff events, and server admission.
- Found no GUI source changes. Existing user deletions and the exercise
  executor's external unstaged edits remain outside this batch.
- Next action: apply only the campaign contract fixes and add focused checks;
  no device input will be used during static implementation.

### Static test environment note

- `pytest -q ...` was unavailable because the shell did not have the virtual
  environment activated. The next attempt uses the repository `.venv` Python
  executable; no code failure was observed in the first attempt.
- `pre-commit run --files ...` was likewise unavailable on PATH; the next
  attempt uses `.venv\\Scripts\\pre-commit.exe`.

## 2026-09-01 Campaign Implementation and E2E

- Added campaign fleet-id propagation, actual-member result mapping, explicit
  destroyer type-OCR bypass, panel and battle handoff events, and Processor
  controlled continuous-page reuse.
- Moved support implementation ownership to `application.combat.support` and
  removed the support export from the legacy campaign facade.
- Added the campaign E2E case and simple destroyer fixture; corrected the
  shared 720p choose-ship signature after the first device failure.
- Static gates: campaign/exercise pytest `41 passed`; choose-ship signature
  regression `1 passed`; targeted Ruff/format and pinned pre-commit passed;
  compileall and `git diff --check` passed.
- Device runs: first run failed before battle due stale choose-page signature;
  the next six single-round scenarios and one two-round run completed. The
  final continuous-reuse code was changed after the two-round run, so that
  exact runtime behavior remains unverified until the daily quota refreshes.
- Device logs are under `logs/e2e_tools/campaign/20260901_022134` through
  `20260901_030737`; the report will link the complete batch summary.
- Pinned pre-commit initially fixed report Markdown trailing whitespace; the
  immediate rerun passed every hook.
- Backend checkpoint committed as `270142a`
  (`feat(campaign): finish sakuya campaign slice`). The backend working tree
  still intentionally contains only the user's unstaged exercise executor
  edit; deleted documents remain untouched.

## 2026-09-04 Governance and Decisive Smoke

- Confirmed the independent task book includes the two appended decisive tasks
  and the standard exercise YAML contract.
- Fixed the decisive smoke tool to use the current controller constructor and
  configured serial display.
- Made `launch_for_test` always run `ensure_ready`, including OCR-enabled runs;
  corrected the startup recovery import to the application navigation service.
- Restricted the Ex-1 waiting-state correction to chapter 1 and stopped waiting
  for a fleet overlay when the map remains a normal recovery page.
- Replaced the stale decisive map template check with the current map pixel
  signature.
- Decisive smoke log: `logs/e2e_tools/decisive/20260904_smoke_success2/`.
  Ex-6 entry, node recognition, fleet OCR, `task_type='decisive'` fleet branch,
  first battle, settlement, and node progression ran; the second node stopped
  on preparation-page/fleet-asset state and returned `ERROR`.
- Added `docs/features/decisive-smoke-report.md` and updated the independent
  task book with the exact result and residual risk.
- Final focused pytest completed with `187 passed in 6.71s` using
  `--basetemp .pytest-tmp-sakuya`; no full pytest was run.
- Task status is now `done`; the partial multi-node decisive smoke remains an
  explicit follow-up requiring valid battle-fleet assets.

## 2026-09-04 Decisive Business Migration

- Added `business/combat/decisive/` and moved the old decision state machine
  (`base`, `chapter`, `config`, `handlers`, `logic`, `state`) under the business
  domain. The former controller implementation now lives in `executor.py`.
- Added `DecisiveExecutor(BaseExecutor)` as the single business entry and
  registered `decisive` in the Processor registry.
- Changed `_start_decisive` to build a typed `Request` and use the same Processor
  path as exercise and campaign; `_processor_details` now maps `DecisiveResult`.
- Reduced `ops/decisive` to an import compatibility shell; no new business code
  imports the old package. The dynamic dock-full destroy call remains a later
  migration item.
- Updated decisive route regression tests and added the business entry test.
- Focused static tests: `169 passed in 7.34s`; limited pre-commit, compileall and
  diff checks passed.

## 2026-09-05 First Coarse Layer Governance

- Audited the bound backend worktree and confirmed the five-package root.
- Removed the empty `business/navigation` forwarding package and updated all
  business callers to use `application.ui.navigation`.
- Added `common/contracts/task.py` for `TaskPaused` and `TaskStopped`; dispatch
  keeps its public re-export while business imports the lower contract directly.
- Changed `dispatch.registry` from import-time business self-registration to an
  explicit lazy `(module, class)` table; removed registration calls from all
  business executors.
- Added root/import-direction regression coverage in
  `testing/architecture/test_layer_packages.py` and aligned the architecture
  and executor-style documents with the new ownership.
- Verification: focused pytest `77 passed in 6.77s`; compileall passed; targeted
  pre-commit passed; `git diff --check` passed. The all-changed-files pre-commit
  run still reports inherited Ruff findings in legacy tests/tools.
- Backend checkpoint: `13d1938` (`refactor(architecture): enforce five-layer
  package boundaries`).

## 2026-09-05 Business Domain Split

- Moved `normal_fight.py` and `event_fight.py` to
  `business/combat/bettle`; added the package export entry.
- Moved the campaign compatibility runner to
  `business/combat/campaign/compat.py`.
- Moved build, cook, and destroy operations to `business/logistics`.
- Moved `business/system/initialize` to `application/runtime/initialize` and
  updated all production/tool/test callers.
- Removed the empty `business/legacy_ops` and `business/system` packages and
  corrected stale migration comments.
- Verification: compileall, canonical import smoke, and affected pytest all
  passed (`225 passed`); targeted production pre-commit passed; diff checks
  passed.
- Backend checkpoint: `8af89e2` (`refactor(business): split combat and
  logistics domains`).

## 2026-09-05 Combat Shared Fleet Flattening

- Flattened `business/combat/fleet` to `business/combat/fleet.py` and moved
  `FleetPolicy` to `business/fleet_policy.py`.
- Preserved `autowsgr.business.combat.fleet` imports and removed only the
  redundant package wrapper.
- Updated architecture checks and combat application documentation; corrected
  the canonical fleet OCR log assertions.
- Verification: compileall, targeted pre-commit, and `git diff --check` passed;
  final focused pytest passed `585` tests.
- Backend checkpoint: `61fbe42` (`refactor(combat): flatten fleet rule modules`).

## 2026-09-05 Shared Combat Boundary

- Moved runtime executor control, combat history/result records, and generic
  phase handling below the business layer.
- Rebuilt `business/combat/handlers.py` as a business-only mixin for rule
  decisions and result interpretation; application supplies common phase
  mechanics and lifecycle hooks.
- Updated business exports and affected tests to canonical application paths.
- Verification: final focused pytest `604 passed`; compileall, targeted
  pre-commit, and `git diff --check` passed.
- Backend checkpoint: `6fd24cc` (`refactor(combat): separate application phase
  handling`).

## 2026-09-05 Handler and Runner Follow-up

- Started after review found that the business handler file and business
  engine assembly were still monolithic.
- Split business handlers into `handlers/decision.py` and
  `handlers/settlement.py`, with `handlers/__init__.py` preserving the public
  `PhaseHandlersMixin` composition entry.
- Renamed the business engine assembly to `business/combat/runner.py` and
  exposed `CombatRunner`; the package-level `CombatEngine` name remains only
  as a compatibility alias while the implementation owner is application.
- Updated focused tests and combat architecture documentation. Focused pytest
  passed `205` tests; normal/scheduler runner coverage passed `67` tests.
- Compileall, import smoke, targeted pre-commit, and `git diff --check` passed.
- User-deleted feature documents and unrelated meta worktree changes remain
  untouched and unstaged.

## 2026-09-05 Bettle Unified Entry

- Began after review found that `business/combat/bettle` had no Processor
  executor despite normal and event flows sharing one Runner.
- Added `business/combat/bettle/executor.py` and registered both
  `normal_fight` and `event_fight` task types against it.
- Passed task type through `BaseExecutor`; the shared `NormalFightRunner` now
  selects navigation explicitly and accepts the Processor wait hook.
- Kept old convenience functions and the event wrapper as compatibility calls;
  normalized the shared bettle log prefix to `[Bettle]`.
- Focused tests passed: `91` unified-entry/dispatch/server tests and `207`
  combat/business/architecture tests. Compileall, import smoke, targeted
  pre-commit, and `git diff --check` passed.
- Backend code is staged for checkpoint commit; user-deleted feature documents
  remain unstaged.

## 2026-09-05 Remove UI Compatibility Layer

- Started after inventory showed `application/ui/legacy` is only the old-path
  compatibility layer and duplicates canonical page registration.
- Redirected all production, test, tool, and example imports to canonical
  `pages`, `navigation`, or `common.ui.interaction` modules.
- Deleted the entire `autowsgr/application/ui/legacy` tree (45 tracked files).
- Removed stale compatibility wording and updated the active architecture
  notes; `pages/decisive/legacy_fleet_change.py` remains as a live optional
  algorithm, not a path compatibility shim.
- UI/ops tests passed `358`; server/dispatch/combat/business tests passed
  `310`. Compileall, canonical import smoke, residual-path search, targeted
  production pre-commit, and `git diff --check` passed.
- The all-changed-files pre-commit run still reports inherited Ruff findings
  in `tools/check_sortie_api.py` and `tools/e2e_chapter_nav.py`; no unrelated
  complexity cleanup was included.
- User-deleted feature documents remain untouched and unstaged.

## 2026-09-05 Navigation Service Split

- Moved `identify_current_page`, its retry constants, and `_sync_ctx_page` to
  `application/ui/navigation/recognition.py`.
- Kept `goto_page` and `_goto_page` as the only service functions; the package
  export remains stable.
- Navigation/startup/stack regression tests passed `66`; compileall, import
  smoke, targeted pre-commit, and `git diff --check` passed.
- The user's unstaged `navigation/registry.py`, `navigation/stack.py`, and
  deleted feature documents remain untouched.

## 2026-09-05 Navigation Ownership Cleanup

- Started after review found the public API and navigation support modules
  still expose mixed responsibilities and compatibility exports.
- Split navigation graph edges into common, combat, and logistics packages;
  moved recognition out of the registry and made the stack state-only.
- Removed the old registry recognition/interaction exports and `UIStack.resync`;
  callers now use canonical recognition and common interaction modules.
- Explicitly grouped package exports for business, E2E/debug, and pytest users.
- Focused navigation and architecture checks passed (`48 passed`), targeted
  pre-commit, compileall, and `git diff --check` passed.

## 2026-09-05 Navigation Governance Follow-up

- Created the independent navigation governance task book and project style
  document in the meta worktree.
- Reworked navigation file headers, one-line action docstrings, numbered flow
  comments, and `# -- ... ------------` section markers.
- Audited the complete graph-to-page-to-common chain and recorded direct and
  transitive common dependencies in `findings.md`.
- Completed the navigation/UI boundary decision: keep existing
  `application/ui/pages` as the semantic UI entry and do not add a generic
  operations forwarding layer.
- Final report written to `[报告]navigation-governance-report.md`; all taskbook
  items are complete and no real-device E2E was used.
- Reworked the navigation comments again after review: file headers now use
  plain business language with canonical dependency paths, functions describe
  business actions, and section markers follow the Unicode project standard.
- Final focused checks passed: 48 pytest cases, pre-commit, compileall,
  blank-line/style scan, and `git diff --check`.

## 2026-09-06 UI Controller Reorganization

- Created and re-read `[任务书]ui-controller-reorganization-task.md`.
- Recorded the baseline: 61 page Python files and approximately 400 old package
  references. No backend code has been changed for this task yet.
- Re-read the task book after the dependency audit. The next batch is the
  physical page move and import-path update; navigation behavior remains frozen.
- An import smoke caught a cycle after an attempted `controller/shared` fleet
  move. The fleet-change package was returned to the battle-preparation
  Controller; shared tabbed-page and ship-selection modules remain in `shared`.
- Moved the page tree to `application/ui/controller`, moved tabbed-page and
  ship-selection capabilities to `controller/shared`, and removed the old
  `pages` package and calibration-only battle-preparation exports.
- Moved generic blood recognition to `common/vision/blood.py`, map counter OCR
  to `common/vision/map.py`, and map calibration values to
  `common/calibration/map.py`.
- Full changed-file pre-commit exposed 16 inherited Ruff findings in four old
  E2E tools. The scoped run excluding those files passed every hook.
- Final verification: compileall passed, canonical imports passed, the sortie
  contract tool passed, old package-path search passed, navigation path-only
  comparison passed with the shared chooser mapping, `git diff --check` passed,
  and focused pytest passed (`318 passed in 12.47s`). No device E2E or full
  pytest was run.
- Ponytail audit found and the main agent fixed the moved tabbed-template root
  (`parents[4]`) and the map-counter `None` comparison. It also confirmed that
  fleet-change stays beside battle preparation to avoid an import cycle.
- Final report: `docs/features/ui-controller-reorganization-report.md`.
- Backend checkpoint: `ec919ec` (`refactor(ui): reorganize page controllers`).

## 2026-09-06 UI Calibration Downshift

- Audited the current calibration diff against the architecture minutes and
  found that the new aggregate `common/calibration/ui.py` is too broad and
  still stores calibration in Python code.
- Recorded remaining hard-coded UI coordinates and the decisive reward-click
  regression in `findings.md`; next step is to move them into page-organized
  common YAML/accessors before running tests.
- A one-off PowerShell `python -c` AST inventory failed during quoting before
  reading source; no files changed. Continued with targeted `rg` and file
  inspection instead of repeating the same command.

- Follow-up requested after review found that most UI page constants still
  lived in Controller modules. This phase will move physical calibration and
  visual thresholds while keeping page semantics and workflow policy above
  common.

## 2026-09-06 Worktree Preservation

- Created the canonical paired `meta` and `AutoWSGR` worktrees for task
  `20260830-sakuya-exercise-consolidated-7a6c`.
- Registered and verified both worktrees for this Agent.
- Applied all 16 tracked changes and copied the untracked
  `bath_page/constants.py`; the original nested worktree was left unchanged.
- Quarantined the stale duplicate Git admin record without deleting it; the
  active `meta` worktree now has one registration.
- Added `[规范]autowsgr架构改造交接.md` with the old-Agent release and new-Agent bind/verify
  commands, and added its precise `.gitignore` exception.

## 2026-09-07 BathPage Review Handoff

- The Bath-specific constants review item was rejected because the constants are
  private to `bath_page` and only used within that module.
- Deferred the `BathPage` OCR/context ownership issue to a dedicated context
  debugging topic; no production code was changed in this review step.
- Added `[todo]上下文问题汇总.md` with the observed `ctx.ocr` bypass, scope,
  and acceptance evidence for the later topic.

## 2026-09-07 BathPage Review Confirmation

- Confirmed with the user that the longest repair item is always the leftmost
  item in the game repair list.
- Closed the `repair_longest` global-selection concern as contract-valid; no
  production code or test changes were made in this review step.

## 2026-09-07 OCR Compatibility Ledger

- Deferred OCR module optimization as requested; current private matcher behavior
  remains unchanged.
- Added `[todo]其他模块与OCR模块之间的兼容冲突.md` covering all four external
  private matcher callers and the future public raw-text matching contract.

## 2026-09-07 UI Controller Rewrite Task

- A1 completed: `click_repair_all()` now requires the post-action screen to be a
  recognized BathPage without the repair overlay, including after manual close.
- A1 checks passed: targeted `compileall`, close-state source assertions, and
  `git diff --check`.
- `ruff check` and `uv run --no-sync ruff check` were unavailable because no
  Ruff executable is installed; no further retry was made. The latter created
  only the worktree-local `.venv` environment.

## 2026-09-07 UI Controller Sample Baseline

- A2 completed: read `[规范]navigation-code-style.md` and inventoried the
  current `bath_page` sample plus all three target page consumers.
- Confirmed the three targets have no OCR-owned code, so the rewrite will not
  create empty `recognition.py` files.
- Recorded the hidden build-page coordinate dependency in
  `ShipType.relative_position_in_destroy` for migration into build constants.
- An initial PowerShell read of `[规范]navigation-code-style.md` used a wildcard
  path and failed; the file was reread successfully with `-LiteralPath` and no
  source files changed.

## 2026-09-07 UI Controller Module Standard

- A3 completed: created `[规范]ui-controller-code-style.md` and added its
  precise meta Git whitelist entry.
- The standard defines page-package boundaries, private normalized constants,
  OCR-only recognition files, business action prefixes, and function ordering.
- The first completeness check searched for the wrong heading (`函数顺序`); a
  corrected check confirmed the actual `def` ordering section and all required
  rules. No source files changed during the failed check.

## 2026-09-07 Build Page Rewrite

- Build subphase completed: moved the controller into the `build_page` package,
  added private normalized constants and package exports, migrated all direct
  callers, and removed the unused public calibration wrapper/YAML.
- Renamed build page predicates/state reads to `check_current_page` and
  `read_active_tab`; normalized destroy action names and moved ship-type filter
  coordinates out of `ShipType`.
- Checks passed: targeted `compileall`, AST/structure assertions, and
  `git diff --check`.
- Direct build import could not run because the environment lacks `cv2`.
  Coordinate-loader evaluation could not run because the environment lacks
  `yaml`; normalized values were verified from the source YAML and existing
  calibration loader contract instead. No dependency was added.
- Two early large `apply_patch` attempts failed on stale whitespace/docstring
  context; they made no changes and were replaced with smaller patches.

## 2026-09-07 Backyard Page Rewrite

- Backyard subphase completed: moved the controller into the `backyard_page`
  package, added private normalized coordinates and exports, updated all
  `BackyardPage`/`CanteenPage`/navigation/test predicate references, and
  removed the unused backyard calibration wrapper/YAML.
- Checks passed: targeted `compileall`, structure assertions, old-symbol scan,
  and `git diff --check`.
- The old `CanteenPage.is_current_page` reference reported by the scoped scan is
  intentionally left for the canteen subphase, where that module is moved.

## 2026-09-07 Canteen Page Rewrite

- Canteen subphase completed: moved the controller into the `canteen_page`
  package, added private normalized coordinates and exports, updated callers,
  and removed the unused canteen calibration wrapper/YAML.
- Renamed the page predicate to `check_current_page` and the animation action
  to `click_skip_animation`; kept the cooking workflow and return behavior.
- Checks passed: targeted `compileall`, structure/coordinate assertions, old
  symbol scan, and `git diff --check`.

## 2026-09-07 UI Controller Rewrite Complete

- A4 completed for build, backyard, and canteen. All three package structures,
  callers, navigation registration, and old calibration references were
  statically checked.
- No empty `recognition.py` was created because none of the three pages owns
  OCR logic; page template checks remain in `page.py`.
- Python runtime import smoke was unavailable because the environment lacks
  `cv2` (and the old coordinate loader lacks `yaml`); `compileall` and AST
  checks passed instead. No dependency was added.
- An A4 completion patch initially targeted the same task file twice and was
  rejected before writing; the updates were split into valid patches.

## 2026-09-07 Comprehensive Report

- A6 completed: added `[报告]ui-controller样板重构综合报告.md` for manual
  review, including scope, changed areas, verification results, TODO ledgers,
  and residual risks.
- Final static checks passed: target compileall, old-reference scan,
  structure/coordinate assertions, new-package line width, and
  `git diff --check`.
- Runtime import, YAML loading, Ruff, pre-commit, pytest, and emulator/device
  checks remain explicitly unverified as documented in the report.
- The first report-content check searched for a missing literal `A5`; the
  corrected check used the actual `Ponytail` heading and passed.

## 2026-09-07 Ponytail Audit

- A5 audit completed: no speculative abstraction, new dependency, duplicate
  compatibility layer, empty `recognition.py`, or unowned state source was found.
- Confirmed the three targets introduce no new context/OCR issue; updated both
  existing `[todo]` ledgers and reserved other residual risks for the report.
- Ponytail static checks passed: forbidden old imports/names absent, target
  packages compile, and `git diff --check` passes.
