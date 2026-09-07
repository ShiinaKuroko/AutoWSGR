Task ID: `20260830-sakuya-exercise-consolidated-7a6c`
Task Status: `in_progress`
Next Step: Downshift remaining UI calibration constants into common.
Previous Step: Complete the Controller move, common downshift, and focused verification.
`server`, `dispatch`, `business`, `application`, and `common` remain at the
architecture root. Do not create a second worktree for this task.

## Active Worktree (2026-09-06)

- Continue this task in the paired worktrees under the project `.worktrees`
  directory: `meta` and `AutoWSGR`, both on
  `codex/20260830-sakuya-exercise-consolidated-7a6c`.
- The original nested worktree is preserved as a read-only source copy for the
  uncommitted exercise changes; do not resume edits there.

## 2026-09-06 UI Controller Reorganization

- [x] Create `[任务书]ui-controller-reorganization-task.md`.
- [x] Inventory and classify all `application/ui/pages` code.
- [x] Move real page operations to `application/ui/controller` and adjust imports.
- [x] Verify boundaries, focused tests, formatting, and deliver the report.

## 2026-09-06 UI Calibration Downshift

- [ ] Inventory all Controller constants and separate calibration from page
  semantics and workflow policy.
- [ ] Move fixed coordinates, colors, signatures, probes, ROIs, and visual
  thresholds to common calibration/vision ownership.
- [ ] Update every Controller, production caller, test, and tool to use the
  canonical common modules without adding forwarding wrappers.
- [ ] Verify imports, focused behavior, formatting, and report residual policy
  constants.

## 2026-09-05 Navigation Governance Follow-up

- [x] Create and follow an independent navigation governance task book.
- [x] Normalize graph layout, comments, and blank-line formatting.
- [x] Audit graph-to-common calls and the navigation/UI operation boundary.
- [x] Record the reusable project style and deliver the final report.

## 2026-09-05 Navigation Comment Path Follow-up

- [x] Rewrite module and function comments with canonical dependency paths.
- [x] Apply the user's Unicode section-marker format, re-read the task book,
  run navigation checks, and update the report.

## 2026-09-05 Combat Handler and Runner Cleanup

- [x] Split `business/combat/handlers.py` into decision, settlement, and
  composition modules.
- [x] Rename the business-side engine assembly to `business/combat/runner.py`;
  keep the state-machine implementation in application.
- [x] Update imports, focused tests, and architecture documentation.
- [x] Run focused pytest, compile/import checks, formatting, and diff checks.

## 2026-09-05 Bettle Unified Entry

- [x] Add one `bettle/executor.py` entry for normal and event combat.
- [x] Pass `task_type` through Processor and select the navigation mode in the
  shared combat runner.
- [x] Keep legacy convenience functions as thin callers and add focused
  Processor/entry coverage.
- [x] Run focused tests and static checks, then record the checkpoint.

## 2026-09-05 Remove UI Compatibility Layer

- [x] Update production, tools, examples, and tests that still import
  `application.ui.legacy`.
- [x] Delete `application/ui/legacy` and remove stale compatibility references.
- [x] Run the affected UI/combat/logistics tests and static checks.

## 2026-09-05 Navigation Service Split

- [x] Move page recognition/retry and context synchronization out of
  `navigation/service.py`.
- [x] Keep only `goto_page()` and `_goto_page()` in the service module while
  preserving the public package export.
- [x] Add an architecture assertion and run navigation regression checks.

## 2026-09-05 Navigation Ownership Cleanup

- [x] Split graph edges into public, combat, and logistics domain modules.
- [x] Keep page registration in `registry.py`, recognition in
  `recognition.py`, and state-only behavior in `stack.py`.
- [x] Group `navigation/__init__.py` exports for business, tools, and tests;
  remove compatibility re-exports.
- [x] Move callers to canonical module paths and run navigation regressions.

## Branch Binding

- Agent ID: `01a0446f-5999-7bc2-aa74-fc1a2887a8a9`.
- Development branch: `codex/20260830-sakuya-exercise-consolidated-7a6c`.
- Development worktree: `C:/ShiinaKuroko/01.Project/.worktrees/20260830-exercise-team-contract-4c71/AutoWSGR`.
- Canonical meta and backend branch: `codex/20260830-sakuya-exercise-consolidated-7a6c`.
- The previous architecture-audit and exercise-migration branches were
  consolidated into this branch and their local refs/worktrees were removed.
- The backend result is already fast-forwarded into `ShiinaSakuya` at
  `3ccd887`.

# Task Plan: Complete Sakuya Exercise Migration

## Goal
Migrate the complete exercise task chain into the Sakuya architecture with the
smallest functional code path, including fleet selection, OCR validation,
handoff checks, interruption points, logs, and result reporting.

## Hard Constraints
- `meta/architecture-upgrade-minutes.md` is the controlling architecture record.
- Sakuya is replacement-mode; old exercise dependencies may be broken or
  removed, but the new path must not depend on both old and new execution paths.
- No GUI source or final GUI/backend contract changes in this slice.
- Static validation must pass before any real-device E2E run.
- At most five real-device E2E attempts; record each attempt and stop using an
  attempt when its result is deterministically established.
- Always initialize from the home page, recover abnormal game exits, and clean
  up back to home at the end of every E2E case.
- Never transfer this branch-local `AGENTS.md` to another branch.

## Phases
- [x] Inventory current Sakuya and Kuroko exercise chains and freeze reusable
  boundaries.
- [x] Repair the infra page import boundary needed by the exercise slice.
- [x] Implement the minimal Sakuya exercise executor, fleet/OCR capabilities,
  navigation handoff checks, and required logging.
- [x] Add focused static tests for admission, execution steps, fleet rules,
  OCR outcomes, interruption points, and result/event semantics.
- [x] Run static gates: focused tests, compile/import checks, Ruff, diff checks,
  and relevant full regression checks.
- [x] Run up to five real-device E2E attempts only after static gates pass.
- [x] Write the migration and E2E report, commit the code and coordination
  records, and leave unresolved compatibility gaps explicit.

## Non-Goals
- GUI visual/layout/interaction changes.
- Full migration of ordinary sortie, expedition, mission, or other business
  domains.
- New OCR/model-training dependencies or YOLO integration.
- Rebuilding the entire Navigator or RuntimeSession beyond what exercise needs.

## Inherited Audit History

# Task Plan: Audit Sakuya Architecture

## Goal
Assess the local Sakuya architecture proposal against the current backend,
identify ownership, lifecycle, contract, and migration defects, and define a
smallest safe implementation sequence for the long-term upgrade.

## Scope
- Backend local `ShiinaSakuya` baseline and its WIP `dispatch/business/infra` tree.
- Current Kuroko is a read-only compatibility reference.
- No release branch, GUI code, or public contract changes in the audit phase.

## Phases
- [x] Inventory current Sakuya architecture and production entry points.
- [x] Map state/lifecycle/contract ownership and rank concrete defects.
- [x] Record migration gates and the first safe vertical slice.
- [x] Present the design findings before implementation.

## User-Approved Operating Model

- Sakuya is a replacement implementation branch; intermediate slices may break,
  delete, or rewrite the old framework and do not need to keep Kuroko runnable.
- Work proceeds one complete vertical feature slice at a time, with short smoke or
  simulator verification during iteration and focused unit tests added after
  acceptance. Full pytest/lint is a milestone gate, not a per-commit gate.
- The Sakuya architecture-upgrade `AGENTS.md` is branch-local and must never be
  synchronized to Sakuya/Kuroko/main or release/PR branches.

## Current Architecture Discussion

- [x] Define the dispatch, navigation, and business ownership boundaries.
- [x] Confirm the business use-case package organization and combat split.
- [x] Review the infrastructure layer: runtime/session ownership, device, vision,
  physical UI, assets, configuration, and legacy migration direction.
- [x] Confirm the code name for the 港区 business domain: `homeport`.
- [x] Define the constant/calibration split and the scoped task/runtime/game-state
  ownership model.
- [x] Define the first exercise vertical slice after those boundaries closed.

## Implementation Phase: Exercise Vertical Slice

- [x] Record the user's final control-plane and lifecycle decisions.
- [x] Harden the E2E initialize/home/cleanup flow and reuse the existing
  screenshot/OCR debug entry points.
- [x] Implement YAML admission and immutable task normalization for exercise.
- [x] Connect CLI/HTTP exercise commands to the Processor.
- [x] Implement finite repeat count, pause/resume, stop, retry, and result count
  semantics in the Processor.
- [x] Verify the complete test path and record residual compatibility gaps.

## Residual Scope

- Real-device E2E was not run on this host; the reusable lifecycle and recovery
  contract are covered by focused tests.
- HTTP requests still use the existing single-worker `TaskManager`; cross-request
  insertion while another HTTP task is running remains a later integration slice.
- Three pre-existing repair tests import the removed `autowsgr.ops.repair` module;
  restoring that compatibility is intentionally outside this exercise slice.

## Historical Context

## Historical Task: Restore combat-drop logs and GUI log storage

## Goal
Restore backend combat-drop log forwarding and ship statistics in AutoWSGR-GUI, and make its configured NAS log directory take effect.

## Next Step
Deliver the verified fixes and documented test limitations.

## Current Phase
Phase 5

## Phases
### Phase 1: Discovery
- [x] Inspect both repositories' constraints, current state, and log-related code
- [x] Trace all consumers of `[Combat] 获得舰船`
- **Status:** complete

### Phase 2: Minimal Change Plan
- [x] Identify root causes and affected callers
- [x] Present cross-boundary changes for confirmation if required
- **Status:** complete

### Phase 3: Implementation
- [x] Apply the smallest shared fixes
- [x] Add focused regression coverage
- **Status:** complete

### Phase 4: Verification
- [x] Run focused checks and inspect the diff
- [x] Record remaining manual-runtime verification
- **Status:** complete

### Phase 5: Delivery
- **Status:** complete

### Phase 6: GUI Packaging Preflight
- [x] Read current GUI/backend versions and package scripts
- [x] Check personal and upstream tags/releases through SSH/API
- [x] Diagnose stale Alpha backend pin and rerun GitHub packaging
- **Status:** complete
- [x] Summarize changes and verification results
- **Status:** complete

## Key Questions
1. Where is `[Combat] 获得舰船` emitted, transported, filtered, and consumed?
2. Why is the GUI custom log path ignored, particularly for a UNC NAS path?
3. Can the three symptoms be fixed in existing shared log plumbing?

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Investigate end-to-end before edits | The reported display and statistics regressions share a likely log-contract dependency. |
| Hold code writes until the batch scope is evidenced | Both repository instructions explicitly require confirmation for multi-boundary changes. |
| Fix combat logs at the backend sink lifecycle | GUI parsing and filtering are healthy; compensating in the GUI would duplicate a broken transport contract. |
| Keep generic file IPC restrictive | A dedicated GUI-log capability can allow only the configured log root without granting arbitrary Renderer writes to NAS paths. |
| Dispatch WebSocket sends on the FastAPI loop | The current sink's private loop is unsafe for FastAPI WebSocket objects created on the application loop. |

## 2026-08-31 Campaign Migration Slice

- [x] Trace the Kuroko campaign chain through HTTP, Processor, scheduler, map,
  battle preparation, combat, and result conversion.
- [x] Add `business/combat/campaign` with `CampaignSpec`, page operations, and
  `CampaignExecutor`; keep repeat count in Processor.
- [x] Move campaign calibration values to common read-only resources and wire
  the campaign task registry, server route, and daily trigger.
- [x] Validate fleet sources at admission and preserve the legacy `ops` facade
  as a thin forwarder.
- [x] Run focused regressions, full pytest, pre-commit, compile/import checks,
  diff checks, and `uv build`.

Non-goal: no real-device campaign E2E was run in this slice; the user only
requested migration and static verification.

## 2026-08-31 Campaign Fleet Rules Slice

- [x] Add a campaign-only preparation-page branch selected by `task_type`.
- [x] Keep campaign physical slots fixed: point-to-point replacement, no card
  drag and no left compaction after removal.
- [x] Encode hard campaign slot types and counts; validate current fleets when
  no explicit names are supplied.
- [x] Preserve the existing normal/event/exercise fleet algorithm and pass the
  exercise task type through its call path.
- [x] Run only campaign/exercise pytest and targeted formatting/lint checks.
- [x] Commit the implementation as backend `22e314e`.

Non-goal: no full repository pytest or real-device E2E was run for this slice.

## 2026-08-31 Campaign Architecture and E2E Plan

### Architecture corrections

- Review the whole path instead of optimizing only the exercise path. Remove
  executor-local `goto` wrappers where the shared Navigator already provides
  the capability.
- Let the ship-selection module expose one entry point; keep recognition and
  selection implementation in application, with business supplying rules.
- Use one consistent log format: `[Module] message`. A module name is either
  all English or all Chinese, never mixed within one path.
- Rewrite comments with short, concrete wording following the user's revised
  exercise-executor style.
- Keep `task_type` in the campaign and exercise context passed to fleet
  preparation. Normal, event, and exercise tasks retain the existing generic
  fleet algorithm.
- Move campaign support-switch code out of the campaign business package into
  the combat-engine capability. Its comment is:
  `确保军阶战役支援开关处于目标状态。`

### Campaign business contract

1. The business layer receives a Processor request and validates the YAML.
2. A valid definition stores its task type for the execution attempt.
3. The shared Navigator reaches the campaign entry.
4. The runtime context is initialized.
5. Read campaign mode (simple/hard), chapter (destroyer/cruiser/battleship/
   carrier/submarine), and fleet configuration. An empty fleet uses the current
   fleet. Backend users may provide complete `name + ships`; GUI users may
   provide only a team `name`.
6. A name-only team must resolve to a team YAML in either the user's config
   directory or the system preset directory. The exact GUI/backend contract is
   a TODO for the final integration slice. Tests use complete fleet definitions.
7. Detect the campaign mode, switch it when needed, and enter the chapter.
8. Enter preparation with `task_type='campaign'`, then use campaign point-to-
   point fleet preparation with the existing OCR implementation.
9. Return to the executor and run the combat engine; wait for battle end and
   record the campaign count.
10. Processor decides whether the next queued task can reuse the campaign
    page. If an inserted task is next, return to the home anchor first.

### Campaign fleet rules

- Slot 1 is mandatory.
- Campaign slots are physical and do not compact left after removal. A fleet
  such as `123456` with slot 1 removed remains `None23456`.
- Campaign preparation cannot drag cards; it only opens a slot and performs a
  point-to-point replacement or removal.
- Every campaign execution with an explicit fleet definition clears all six
  physical slots before filling the requested fleet, so no previous fleet
  member can mask a replacement step.
- Simple campaigns have no ship-type restriction and may contain one ship.
- Hard campaigns require every available slot and enforce these fixed types:
  - destroyer: `DD, DD, DD, DD, DD, DD`
  - cruiser: `BB, CA, CA, CL, CL, DD`
  - battleship: `BC, BB, CA, CA, DD, DD`
  - carrier: `CV, CV, DD, DD, DD, DD`
  - submarine: `SS, SS, SS` only

### Campaign breakpoints and progress

- After navigation reaches the entry.
- When the preparation page is entered.
- After each individual slot replacement.
- After the final replacement, before battle start; this is also the last
  replacement checkpoint.
- When one campaign battle ends, before the next campaign or inserted task.
- Every replacement checkpoint must preserve task progress and fleet state;
  replacement itself has two possible substeps (choose a ship, then optional
  position adjustment). Campaign has no position-drag substep, while the
  generic path keeps its existing reorder behavior.

### Required campaign logs

- `[Campaign] 开始战役任务`
- `[Campaign] 战役战斗开始`
- `[Campaign] 战役队伍加载：使用队伍 {fleet_id}、编队配置加载成功`
- `[Campaign] 战役队伍加载：使用队伍 {fleet_id}、未配置编队，沿用当前队伍`
- `[Campaign] 进入战斗：阵型配置={}，夜战配置={}`
- `[Campaign] 战斗结束，战役结果: {}，已执行战役次数 X，剩余次数 X`

### Test fleet and E2E cases

- Campaign daily quota is eight and refreshes at 00:00.
- Hard destroyer test fleet uses strict name/level validation (all levels
  `>=100`), with the custom name `雪风` and the six listed alternatives for
  every slot: `岛风、早春、阳炎、吹雪、初夏、高波`; the other five primary
  names are `弗莱彻、塞尔弗里吉、明斯克、T-23、吕贝克`.
- Simple destroyer campaign may reuse an existing fleet definition like an
  exercise task.
- E2E checks all campaign breakpoints. After 00:00, insert an exercise once;
  when exercise is exhausted, insert expedition check and reward collection
  in sequence, without repeating the same insertion at every breakpoint.
- E2E verifies ship replacement, campaign point-to-point behavior, simple
  campaign with one ship, and hard campaign fixed slot/count validation.
- E2E starts each configured campaign after clearing the preparation fleet.
- Do not run full repository pytest for this slice; run only exercise and
  campaign pytest plus targeted static checks. Report all runtime and static
  results in the final report.

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Planning-file patch context mismatch | 1 | Re-read the files and applied narrower, correctly targeted updates. |
| Broad GUI search named nonexistent `test` and `tests` directories | 1 | Use known paths and package-script discovery instead. |
| Repeated backend search named nonexistent `tests` directory | 2 | Stop using guessed test directories; inspect package configuration first. |
| Backend runtime reproduction lost quoting in PowerShell | 1 | Rely on static direct call-order evidence; use a different check only if runtime proof remains necessary. |
| GUI `test-main-ipc` fails on an existing updater assertion | 1 | Do not change updater behavior; retain failure evidence and run focused IPC/service coverage. |
| GUI settings test was invoked directly with Node | 1 | Use its Electron package script instead. |
| GUI `test:settings` fails at an existing `guiLogRoot` dirty-state assertion and cleanup reports `EBUSY` | 1 | Do not alter unrelated settings behavior; use dedicated service coverage and report the failure. |
| Narrow Node IPC verification lost JavaScript quotes through PowerShell | 2 | Stop retrying quoting variants; use existing service coverage and static bridge audit. |

## 2026-09-05 First Coarse Layer Governance

- [x] Confirmed `autowsgr` has only the five architecture packages plus the
  ignored Python cache directory.
- [x] Moved old top-level implementations into their responsibility owners:
  application runtime/UI, business legacy operations, dispatch legacy scheduler,
  and common device/vision/system/contracts.
- [x] Removed the business navigation forwarding package; business uses the
  shared application Navigator directly.
- [x] Moved `TaskPaused` and `TaskStopped` to the dependency-free common task
  contract and changed dispatch to re-export the same objects.
- [x] Replaced business self-registration with an explicit dispatch registry
  mapping and lazy class loading.
- [x] Added architecture checks for the five-package root and downward imports.
- [x] Static gates: focused pytest `77 passed`, compileall, targeted pre-commit,
  and `git diff --check` passed. No real-device run was needed.

### Remaining Known Scope

- Existing `legacy` tests/tools still report pre-existing Ruff findings when the
  entire migration diff is passed to pre-commit. The moved runtime files and all
  files changed for this boundary pass clean targeted hooks.
- Historical architecture/usage documents still mention old paths where they
  describe earlier migration events; the current architecture index and
  governance document point to the five-package layout.

## 2026-09-05 Business Domain Split

- [x] Keep only `business/combat` and `business/logistics` as production
  business domains.
- [x] Move normal/event sortie code into `business/combat/bettle` and keep the
  existing campaign compatibility entry beside the campaign executor.
- [x] Move build, cooking, and dismantling operations into
  `business/logistics`; move runtime initialization into `application/runtime`.
- [x] Remove `business/legacy_ops`, `business/system`, and the empty navigation
  package; update production, examples, tools, and affected tests.
- [x] Verify the moved import graph and run the affected suite (`225 passed`).

## 2026-09-05 Combat Shared Fleet Flattening

- [x] Flatten `business/combat/fleet` into `business/combat/fleet.py`.
- [x] Move the cross-domain policy table to `business/fleet_policy.py` and
  remove the redundant package wrapper.
- [x] Align application documentation and architecture regression checks.
- [x] Run compileall, targeted pre-commit, diff checks, and the focused suite
  (`585 passed`).
- [x] Backend checkpoint: `61fbe42`.

## 2026-09-01 Campaign Delivery Checkpoint

- [x] Fix shared choose-ship page signature exposed by the first campaign E2E.
- [x] Verify simple campaign fleet clearing, point-to-point replacement, battle,
  result settlement, and home cleanup.
- [x] Verify all five campaign pause handoff points with expedition/reward
  insertion and resume.
- [x] Add Processor-owned continuous campaign page reuse and regression tests.
- [x] Add campaign E2E case and simple fixture under the new tool path.
- [x] Run campaign/exercise pytest (`42 passed`) and targeted static gates.
- [ ] Re-run device `count=2` after the final reuse-marker fix; the daily quota
  was exhausted by the pre-fix run, so this remains a documented residual.
- [ ] Run the supplied six-slot hard destroyer asset on a refreshed account
  with the required strict name/level checks.

## 2026-09-05 Shared Combat Boundary

- [x] Move `BaseExecutor` runtime pause/stop adaptation to
  `application/runtime/executor.py`.
- [x] Move neutral combat history/result records to
  `application/combat/history.py`.
- [x] Move generic combat phase dispatch, page progression, and terminal actions
  to `application/combat/engine/phase_handlers.py`.
- [x] Keep plan-driven decisions and result interpretation in
  `business/combat/handlers.py`.
- [x] Run compileall, targeted pre-commit, diff checks, and focused pytest
  (`604 passed`).
- [x] Backend checkpoint: `6fd24cc`.
| GitHub fetch cannot connect to `github.com:443` | 1 | Inspect Git/proxy configuration and reachability before retrying a different transport route. |
| SSH-over-443 authentication rejected | 1 | Commit locally; require GitHub SSH identity or restored HTTPS access to push. |
| Direct SSH-over-443 push rejected | 1 | Do not repeat for the GUI; restore credentials or HTTPS access first. |
| Planning-file patch contained an empty hunk | 1 | Reapply only non-empty record updates. |
