# Findings & Decisions

## Requirements
- Restore the GUI home-page display of backend `[Combat] 获得舰船` logs.
- Restore the home-page ship statistics driven by those logs.
- Make the GUI custom log directory work with `\\192.168.31.147\服务器存储\AutoWSGR-GUI\logs` instead of always writing under `%APPDATA%`.

## Research Findings
- The workspace contains separate `AutoWSGR` and `AutoWSGR-GUI` repositories.
- No prior planning-session recovery report was found.
- The task crosses backend log emission and GUI log consumption/configuration; inspect both before selecting a fix.
- Both repositories require `git status --short --branch`, caller/consumer searches, focused regression evidence, and a user-confirmed batch plan before cross-boundary implementation.
- The backend instructions were read in full. The GUI instructions need a line-range re-read because the terminal response truncated the middle section.
- `AutoWSGR` is on `ShiinaKuroko` with a pre-existing untracked `.dbg/` directory; it is outside this task and will be preserved.
- `AutoWSGR-GUI` is on `ShiinaKuroko` with a clean worktree.
- GUI architecture places filesystem/path behavior in Electron services/repositories and cross-runtime transport in IPC/adapters; display/statistics consumers belong in Renderer model/controller/view code.
- GUI minimum verification is selected by the actual boundary changed, including build, renderer-contract, main-service, main-IPC, and API-contract checks as applicable.
- Backend emission exists at `AutoWSGR/autowsgr/combat/handlers.py:578`: `_log.info('[Combat] 获得舰船: {}', ship_name)`.
- Backend WebSocket log routing has a dedicated ship-drop matcher at `AutoWSGR/autowsgr/server/ws_manager.py:27`.
- GUI statistics still parse the same log contract at `AutoWSGR-GUI/src/model/statistics/DailySortieStats.ts:180`, with existing regression coverage in `scripts/tests/test-daily-sortie-stats.mjs`.
- GUI log directory logic is distributed across `src/model/ConfigModel.ts`, `src/controller/app/AppController.ts`, `src/utils/Logger.ts`, Electron IPC, and `electron/services/AppPaths.ts`.
- `WebSocketManager` intentionally filters live log messages to `_STATS_LOG_PATTERNS`; its ship-drop regex still accepts `[Combat] 获得舰船`.
- `DailySortieStats` continues to parse `[Combat] 获得舰船: <name>` and updates both ship count and per-ship drops.
- `AppController` receives backend logs, normalizes the visible message, routes it through runtime/scheduler handling, writes it via `Logger`, and re-renders the main view.
- `AppController.resolveGuiLogDir()` explicitly recognizes Windows drive paths and UNC roots beginning with `\\`; a UNC path itself is not automatically rejected by the renderer-side resolver.
- The observed initialization order appears to initialize `Logger` with `resolveGuiLogDir()` before `configCtrl.loadConfig()`, which is a concrete candidate for the custom GUI log path being ignored. Verify persistence and exact order before selecting a fix.
- `AutoWSGR/autowsgr/server/main.py` installs `ws_manager.build_log_sink()` at server startup; the server-side ship-drop whitelist is therefore active only on the WebSocket log route.
- GUI `AppController` handles `onBackendLog` by normalizing a line, calling `SchedulerBinder.handleBackendRuntimeLog()`, `Scheduler.processBackendLog()`, local `Logger`, and `renderMain()`.
- `DailySortieStats.consume()` is owned by `SchedulerRuntimeTracker`, so the precise input route to that tracker is the key shared dependency for the first and third symptoms.
- GUI custom log-root persistence is implemented by `GuiConfigurationService`, exposed synchronously through `ConfigurationIpc`, read by `IpcAdapter`, and mirrored by `ConfigController`.
- Electron forwards backend child-process stdout/stderr to the Renderer as `backend-log`; `AppController` attaches this to UI logging and the runtime tracker.
- Separately, `ApiClient` opens `/ws/logs`; the server sink emits its whitelisted stat messages there. The two routes must be traced to their consumers before diagnosing display versus statistics behavior.
- `SchedulerBinder.handleBackendRuntimeLog()` feeds `SchedulerRuntimeTracker.consume()`, which feeds `DailySortieStats.consume()`.
- `Logger.init()` is called with `resolveGuiLogDir()` before `loadConfigAndSync()` in the AppController startup callbacks. The main-process synchronous GUI-log-root lookup may still make this correct after a restart, so persistence and append-file authorization remain to be verified.
- The confirmed GUI WebSocket path is `/ws/logs` -> `ApiClient.callbacks.onLog` -> `Scheduler.callbacks.onLog` -> `SchedulerBinder` -> `SchedulerRuntimeTracker.consume()` and `Logger.logLevel()`.
- `Logger.logLevel()` invokes the home-page `LogView`, so one WebSocket message should update both the dashboard statistics and the log panel.
- `LogView` applies an additional non-GUI INFO filtering policy; inspect its exact verbose patterns before excluding client-side suppression as the display failure.
- GUI file writes use `FileIpc` -> `secureFiles.append`, so whether the secure-path policy admits a configured UNC path is now a primary hypothesis for the custom directory failure.
- Root cause for symptoms 1 and 3: FastAPI lifespan registers the WebSocket statistics sink in `autowsgr/server/main.py`, then `/api/system/start` reaches `infra/logger.setup_logger()`, whose unconditional `logger.remove()` removes that sink. The backend still emits the combat line locally, but `/ws/logs` receives nothing.
- `LogView` does not suppress `[Combat] 获得舰船`: its only non-debug verbose filters are unrelated ADB/detector strings.
- Root cause for symptom 2: `resolveGuiLogDir()` accepts UNC and settings persist `gui_log_root`, but `SafePathService.resolveWritablePath()` rejects UNC and all write roots outside userData. `Logger.flush()` discards the resulting rejected append promise, hiding the failure.
- A GUI-log-root setting changed during the running session also cannot take effect because `Logger` has `setLevel()` but no log-directory update; `Logger.init()` sets the directory only once.
- The generic file IPC must remain restrictive: existing `scripts/tests/main-services/test-path-and-file.js` covers UNC and external-path denial. A custom log path needs a dedicated, narrowly scoped writer rather than relaxing `append-file`.
- Updater diagnostics are intentionally separate (`GuiUpdaterLogger`) and must remain under their existing updater/userData path.
- Backend pytest discovery is rooted at `AutoWSGR/testing`; focused server tests live under `testing/server`.
- GUI verification routes available for this task are `npm run test:daily-sortie-stats`, `npm run test:main-services`, `npm run test:main-ipc`, `npm run test:settings`, and `npm run test:build`.
- Backend implementation has added sink lifecycle and worker-thread dispatch coverage; focused pytest passed in the implementation track.
- GUI implementation has added `GuiLogService`, a fixed-filename configured-root writer, while retaining the generic `append-file` safe-path restrictions; its focused main-services test passed in the implementation track.
- Final precheck found all `build_log_sink` callers updated and all new `appendGuiLog` bridge call sites present; neither repository has whitespace errors in its diff.
- Main-thread backend verification passed: `.venv\\Scripts\\python.exe -m pytest testing/server/test_ws_log_sink.py testing/server/test_system_routes.py -q` reported `10 passed`; changed server modules also passed `py_compile`.
- Main-thread GUI verification passed: `npm run test:main-services` (including build) and `npm run test:daily-sortie-stats`.
- Final GUI build-contract verification passed: `npm run test:build`.
- Final diff checks passed in both repositories. The remaining untracked backend `.dbg/` material predates this task and was preserved.
- Both repositories are already on the target `ShiinaKuroko` branch; no branch merge is required before committing this work.
- Remote fetch to both GitHub origins failed because `github.com:443` could not be reached. No commit, push, or staging action has occurred yet.
- No Git or environment proxy is configured. `github.com:443` is blocked, while `ssh.github.com:443` is reachable; SSH-over-443 is the viable alternate GitHub transport.
- SSH-over-443 authentication was rejected with `Permission denied (publickey)`, so this machine currently has no usable GitHub SSH identity.
- Local commits created on `ShiinaKuroko`: AutoWSGR `4a1809a` and AutoWSGR-GUI `7f3c99c`. The backend `.dbg/` directory remains untracked and excluded.
- Direct SSH-over-443 push of the backend commit was rejected with `Permission denied (publickey)`. The GUI push was not repeated because it uses the same unavailable GitHub identity.
- After SSH configuration was restored, AutoWSGR pushed successfully and `git ls-remote` confirmed `ShiinaKuroko` at `4a1809a47b3444a10bfd22e5364b77da4eeac358`.
- The same key is a repository-scoped deploy key for `ShiinaKuroko/AutoWSGR`; GitHub rejected it for `ShiinaKuroko/AutoWSGR-GUI`. No second SSH identity or agent is configured.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Prefer existing log transport/configuration helpers | Required by the local minimal-change policy and likely resolves multiple symptoms at once. |
| Reinstall the backend stats sink after logger configuration | `setup_logger()` must reset backend handlers, so the server-owned sink belongs after that reset. |
| Use the FastAPI lifecycle loop for sink delivery | WebSocket connections and the manager lock belong to that loop; do not send through the sink's private loop. |
| Add a dedicated GUI-log writer | It supports the explicitly configured root while preserving generic file IPC's userData-only capability. |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Initial UTF-8 local instructions rendered incorrectly in PowerShell output | Re-read with explicit UTF-8 encoding before relying on detailed rules. |
| Broad GUI search named nonexistent `test` and `tests` directories | Use known source directories and package-script discovery for later searches. |
| Repeated backend search named nonexistent `tests` directory | Subsequent searches will use discovered paths only. |
| Backend runtime reproduction command lost quoting in PowerShell | Static call-order evidence is sufficient; do not repeat the same shell form. |
| GUI `test-main-ipc` stops at an existing updater assertion (`allowDowngrade`) | Record separately; confirm the new IPC registration through focused coverage and do not alter unrelated updater behavior. |
| GUI settings test run directly with Node lacks Electron `app.commandLine` | Use the package script, which invokes Electron, for the relevant validation. |
| GUI `npm run test:settings` fails at an existing dirty-state assertion for `guiLogRoot`, then its temporary userData cleanup reports `EBUSY` | Do not alter unrelated dirty-state behavior; cover immediate log-root switching through the dedicated service test and report the broader failure. |
| Narrow Node IPC verification lost its JavaScript quotes through PowerShell (twice) | Stop retrying shell quoting variants; rely on the passing service test, compiled call-site audit, and recorded broader IPC-test baseline failure. |
| GitHub fetch cannot connect to `github.com:443` | Inspect local Git/proxy configuration and network reachability before retrying via a different route. |
| SSH-over-443 has no usable GitHub key | Commit locally on `ShiinaKuroko`; push remains blocked until HTTPS access or SSH credentials are provided. |
| Direct SSH-over-443 push rejected | Do not repeat for the GUI; restore a GitHub SSH identity or HTTPS/proxy access, then push the two already-created commits. |
| GUI push rejected because the key is scoped to the backend repository | Add the key to the GUI repository with write access or load an account key, then push `7f3c99c`. |
| Planning-file patch contained an empty hunk | Reapply only the intended, non-empty record updates. |

## Resources
- Packaging preflight: GUI `package.json` and `package-lock.json` are both `2.1.1-alpha.6`; the personal GUI remote already has tag `v2.1.1-alpha.6`, so that version cannot be published again.
- Packaging preflight: upstream GUI tags include `v2.1.0`; upstream and personal backend/GUI release metadata still need explicit API confirmation.
- Packaging preflight: `gh` is unavailable; SSH Git refs and read-only GitHub API requests are the available metadata routes.
- Packaging preflight: backend `autowsgr/__init__.py` reports `2.3.0`; GUI `package.json`/`package-lock.json` report `2.1.1-alpha.6`.
- Packaging preflight: upstream GUI latest stable is `v2.1.0`, upstream GUI has no newer prerelease, upstream backend latest stable is `v2.3.0`.
- Packaging preflight: personal GUI `v2.1.1-alpha.6` is already tagged/released; `v2.1.1-alpha.7` is absent. Builder alpha output is `release/alpha` and uses `--publish never`.
- Packaging preflight API: upstream GUI `yltx/AutoWSGR-GUI` latest release is stable `v2.1.0` (2026-08-15); personal GUI `ShiinaKuroko/AutoWSGR-GUI` latest release is prerelease `v2.1.1-alpha.6` (2026-08-27).
- Packaging preflight API: upstream backend `OpenWSGR/AutoWSGR` latest release is stable `v2.3.0` (2026-08-04); no newer test release was returned. The personal backend release query returned no release entries.
- Packaging candidate: `v2.1.1-alpha.7`, because `v2.1.1-alpha.6` is already released and the current fixes are new commits after it; no version file or tag has been changed.
- Packaging preflight error: the first task-plan update used stale wording and did not apply; no business file changed.
- Packaging preflight: GUI `package.json` reports `2.1.1-alpha.6`; lockfile parsing needs a targeted check because PowerShell `ConvertFrom-Json` failed.
- Packaging preflight: the task-file update needs a narrower anchor; the first broad patch did not apply.
- `AutoWSGR/AGENTS.md`
- `AutoWSGR-GUI/AGENTS.md`

## Visual/Browser Findings
- None.

## GitHub Packaging Result
- Historical run `33040344308` failed at `Verify pinned backend` because Alpha still pointed to `855228a8503474aa3bae292f627b41d783b7a4b7` while `ShiinaKuroko/AutoWSGR:ShiinaKuroko` was at `4a1809a47b3444a10bfd22e5364b77da4eeac358`.
- Updated only `AutoWSGR-GUI/build/backend-distribution.json` Alpha commit, committed as `f92078a`, pushed to `ShiinaKuroko`, and manually dispatched the existing release workflow.
- Run `33105288742` completed successfully from `f92078a`; the existing `v2.1.1-alpha.6` Release now has refreshed `alpha.yml`, installer, and blockmap assets.

## 2026-08-29 Sakuya Architecture Audit

### P0/P1 defects

1. **Processor is not the production scheduler.** `server/routes/task.py:43-71`
   dispatches by request type into private `_start_*` closures and
   `server/task_manager.py:115-345` owns the worker, status, stop signal, and
   lease. `scheduler/scheduler.py:127-154` owns a second queue, while
   `dispatch/processor.py:76-147` is only exercised by tools/E2E. The stated
   "all requests pass Processor" invariant is false and the three paths have
   different lifecycle/result semantics.

2. **Priority ordering is incompatible between the two schedulers.**
   `scheduler/daily_plan.py:6-8,47-57` defines lower numbers as more urgent
   (expedition `0`, bath repair `200`), while `dispatch/processor.py:54-55,119-122`
   negates priority so larger numbers run first. A direct migration would make
   bath repair outrank expedition. A smoke check produced
   `['bath_repair', 'expedition_check']` for priorities `200` and `0`.

3. **The proposed layer graph contains a cycle and legacy back-edges.**
   `business/base.py:27-28` imports `dispatch.processor.TaskPaused`;
   `business/combat/exercise.py:41-51` imports `dispatch`, `ops.startup`, and
   `ui.battle`; new `infra/base/ui/pages/*` modules import `autowsgr.ui.utils`.
   Direct imports of `infra.base.ui.pages.map` and `mission_page` fail with
   circular-import errors. The new layer is therefore not independently usable.

4. **The WIP removes public compatibility modules despite the documented
   compatibility baseline.** `autowsgr/ops/exercise.py`, `expedition.py`,
   `reward.py`, `repair.py`, and `navigate.py` are deleted and are no longer
   exported by `ops/__init__.py`. Direct imports of
   `autowsgr.ops.exercise`, `.expedition`, and `.reward` fail with
   `ModuleNotFoundError`, while `update/cli-usage-inventory.md` requires those
   `ops` APIs to remain stable.

5. **Context and lifecycle ownership remain global and mutable.**
   `server/main.py:40-51` stores `_ctx` in module state; `routes/system.py:38-87`
   publishes/clears it directly and does not disconnect the controller on stop.
   `GameContext` itself still combines controller/OCR/config, mutable fleet and
   registry state, UI stack/current page, daily counters, and task stop state
   (`context/game_context.py:30-128,253-284`). This contradicts the task-local
   context and single-owner goals in the architecture notes.

6. **Sakuya regresses WebSocket and worker lifecycle safety.**
   `server/ws_manager.py:49-51,87-117` uses one connection set for log/task
   streams and holds its lock while awaiting every send. `:177-220` starts a
   private event loop per sink without a close owner. `server/task_manager.py:234-241`
   submits notifications to a loop without checking whether it is closed.
   These are known fixes in current Kuroko and must be ported before migration.

7. **A migrated mission page has a runtime path/import defect.**
   `infra/base/ui/pages/mission_page/data.py:155-162` resolves
   `infra/base/ui/data/missions.yaml`, but the data lives under
   `autowsgr/data/missions.yaml`; its production caller is
   `page.py:156-179`. The module also fails earlier under a direct import because
   of the `ui` cycle.

8. **Chapter navigation loses the dynamic highlighter algorithm.**
   `infra/base/ui/pages/map/base.py:105-108` now returns the fixed `0.556` for
   `find_selected_chapter_y()` and no longer accepts/scans a screenshot, while
   `infra/base/ui/pages/map/panels/sortie.py:164-167` still uses that value to
   locate the target chapter. This is a user-visible navigation regression, not
   a harmless relocation; the old Kuroko implementation scans the highlighted
   sidebar segment. It needs a before/after screenshot regression before any
   map-flow migration.

### Design gaps

- `dispatch/` contains only `processor.py` and `registry.py`; the documented
  command/contract/scheduler/runner/runtime modules and `server/cli` are absent.
- `Request` is a mutable dataclass with plain `dict` params and no schema, task
  identity, deadline, cancellation reason, or typed event/result contract.
- `Processor` has one shared `GameContext`, one global pause event, no task state
  machine, no exception-to-terminal-state policy, and no concurrent `run_pending`
  ownership. There are no deterministic Processor/registry tests; the 1015-test
  Sakuya suite does not exercise this central path.
- Task types/statuses/results are duplicated across `dispatch.Request`,
  `server.schemas`, `server.task_manager`, and GUI DTOs instead of one canonical
  command/event contract.
- `infra/base/data` is an empty declaration; static data still lives in the old
  `autowsgr/data` tree. Coordinate loading duplicates the generic YAML loader and
  returns unvalidated `Any` values from a process-wide mutable cache.
- `business/logistics/repair/quick_repair.py:25-51` accepts a UI page object and
  private `_ctrl` fields, so the business layer is coupled to a concrete UI
  implementation. Several repair paths also catch navigation failures and return
  success-like results, hiding incomplete anchor recovery.
- Sakuya `8745604` is not based on current Kuroko `a475b4a`; it is 12 commits ahead
  and 36 behind. Merging the WIP wholesale would reintroduce fixed lifecycle and
  log behavior.
- `infra/base/ui/navigation.py` also imports old `ui.map`, `ui.sidebar_page`, and
  `ui.event`; the compatibility direction is reversed and must be made one-way.
- The compatibility defect includes top-level exports: `ops/__init__.py` removes
  `collect_expedition`, `collect_rewards`, `repair_in_bath`, `goto_page`,
  `identify_current_page`, and `run_exercise`, not only their submodules.

### Safe restart sequence

1. Freeze Kuroko public routes, DTOs, `ops` imports, config/YAML, and GUI event
   payloads as compatibility tests.
2. Define one canonical command/task/event model and priority direction before
   wiring any production route.
3. Build a single-owner runtime/dispatcher shell with explicit context and lease
   lifetimes; keep old `TaskManager`/`TaskScheduler` as adapters until consumers
   migrate.
4. Use the exercise flow as the first vertical slice because its handoff document
   has concrete pause/anchor acceptance criteria; migrate page dependencies and
   public shims in the same slice.
5. Add deterministic dispatcher, import-order, route-wiring, and compatibility
   tests before enabling the next business flow.

## User Decision: Replacement-Mode Sakuya

- User approved the replacement-mode workflow: Sakuya may break the old framework
  while implementing and optimizing complete new-architecture features; Kuroko
  compatibility is evaluated only at the final replacement/integration gate.
- User approved short per-iteration validation and deferred broad pytest work until
  a feature is accepted; core state/dispatcher/error tests remain mandatory before
  the next slice.
- The architecture branch `AGENTS.md` is intentionally branch-local. Business code
  may be transferred later, but this file must be excluded and the target branch's
  own instructions restored before every merge.

## Sakuya Baseline Sync

- The audit branch shared base `8745604` with `ShiinaSakuya`; Sakuya's current
  merge `16349d20` was integrated as audit-branch commit `8bf5d168`.
- The synchronization included 45 non-`AGENTS.md` code, test, tool, and document
  paths. The audit branch's local `AGENTS.md` remained unchanged and was not
  carried from Sakuya.

## 2026-08-29 Business-Domain Boundary Review

- The current Sakuya tree already proves that normal and event sorties share one
  flow: `EventFightRunner` is a thin `NormalFightRunner` subclass. The final
  replacement architecture should expose one sortie executor with an explicit
  entry/mode specification, not retain a second event runner.
- `ExerciseRunner`, campaign, and decisive battle have materially different
  workflows and should remain separate task executors. Their shared fleet work
  is a real reuse point, but only as small shared capability and policy data,
  not as a common runner base class.
- Existing `business/combat/fleet_policy.py` is the useful seed: policy decides
  eligible fleets and selection rules; page recognition, OCR, and clicking must
  remain in infra. The same policy capability can serve expedition where its
  actual rules overlap.
- Fast repair in battle preparation is not the same use case as bath repair.
  It is an atomic combat-preparation step, has no independent scheduler
  lifecycle, and must not become a queued repair task. Bath repair is a
  separately schedulable homeport operation. Current
  `business/logistics/repair/quick_repair.py` is therefore semantically
  misplaced and also coupled to a concrete UI page and private `_ctrl` fields.
- A runner/executor exists only for a user- or scheduler-submittable operation
  with independent status, cancellation, and result. A required atomic step
  inside another task remains an internal capability. This prevents one runner
  per page or one runner per button.

## 2026-08-29 Infrastructure Inventory

- The current Sakuya infrastructure is transitional rather than a closed layer.
  `autowsgr/infra` contains configuration, logging, exceptions, file utilities,
  constants, and partially migrated physical UI; the device, vision, asset, and
  most physical-page implementations remain elsewhere.
- `infra/base/data`, `infra/base/matcher`, and `infra/base/ocr` are currently
  declaration-only packages. `infra/base/ui/navigation.py` has a useful physical
  graph and BFS, but its edge actions import legacy `autowsgr.ui` page classes.
- `business/system/navigate.py` duplicates navigation ownership by identifying
  pages, retrying, managing `UIStack`, and writing `GameContext.current_page`.
  Its current responsibilities belong in the future shared semantic Navigator,
  while page recognition and actions remain lower-level infrastructure.
- `GameContext` currently combines device/OCR/config references, game snapshots,
  page state, navigation stack, daily counters, task-adjacent counters, and a
  stop event. `server.TaskManager` owns a second stop event. A future
  `RuntimeSession` must own runtime capabilities only; the Processor must own
  lifecycle/cancellation state; game snapshots require their own explicit owner.
- The user confirmed `homeport` as the code-domain name for the game's 港区 domain.
  `port` is rejected because it conflicts with common technical uses such as
  network ports and interface ports.
- `emulator.controller.AndroidController` is already a clean low-level device
  boundary: it exposes connection, screenshots, input, app, and shell actions
  without game/page/OCR imports. The vision package is likewise a reusable
  perception capability. Neither needs a business-facing wrapper in the first
  migration slice.
- Physical UI is the unstable boundary. `ui.page` owns a process-global mutable
  page registry populated as an import side effect by `ui.__init__`; `UIStack`
  holds navigation-session state but is stored on `GameContext`. The future
  Navigator needs one explicitly scoped page catalog and must own its navigation
  state, not leave it as a hidden global plus a context field.
- `server.device_lease` protects a physical shared emulator but is a server
  global. Its eventual owner is the per-runtime `RuntimeSession` (as the device
  resource boundary); Processor uses it but retains ownership of task lifecycle.
- `data` and `image_resources` are package assets/template lookup mechanisms,
  not business use cases. They should remain read-only low-level resources with
  a clear resolver boundary; moving every file merely to satisfy a new directory
  layout would add churn without architectural value.

## 2026-08-30 Vision and Runtime Boundary Proposal

- `homeport` is the confirmed code-domain name for the 港区 business domain.
- CPU-mode CV2 and OCR are complementary rather than interchangeable: CV2 should
  locate/crop/verify stable visual structure, while FastOCR is reserved for text
  and numeric semantics inside a bounded ROI. FastOCR is the intended single OCR
  backend; EasyOCR removal waits for an explicit consumer inventory and slice
  verification.
- YOLO/model training is rejected for the current baseline. It becomes a future
  option only after evidenced CV2 calibration failures across real layouts make
  incremental rules demonstrably unmaintainable.
- UI coordinates, OCR regions, signatures, and template metadata are calibration
  resources, not Python constants. User-editable task YAML and runtime state are
  not package `data`; the backend must validate an allowed YAML path and snapshot
  it into an immutable task definition.
- The proposed `context` ownership is rejected as a monolith: Processor owns task
  lifecycle; RuntimeSession owns runtime resources and device lease; Navigator
  owns navigation state; an explicit game-state owner owns observed game facts;
  an Executor owns only attempt-local state.

## 2026-08-30 Context and Calibration Ownership

- Centralized coordinate access is the right maintenance goal, but business code
  should not become a new consumer of screen geometry. The long-term endpoint is
  a page/infra capability such as `battle_prep.start()`; that capability reads
  the centralized calibration catalog internally. Dotted access is useful inside
  infra and diagnostics, not as a business/UI coupling API.
- The existing `infra/base/constants/coordinates`, `colors`, `ocr`, and
  `signatures` loaders are a useful seed and should be reused. A future typed,
  immutable `UIProfile` can expose grouped namespaces such as
  `session.ui_profile.coordinates.battle_prep.start_battle` and
  `session.ui_profile.ocr.battle_prep.ship_level`, while the YAML remains the
  single calibration source.
- Keep four categories separate: immutable program constants; UI calibration
  data (coordinates, ROIs, colors, signatures); read-only asset/template/model
  resources; and business policy values. A single `Constants` megamodule would
  recreate the coupling it is meant to remove.
- “Context” is a scope/view, not the owner of every mutable fact. The durable
  scopes are: `TaskInstance` (task lifecycle and checkpoint),
  `ExecutionAttempt` (one run's local state), `RuntimeSession` (device, vision,
  UI profile, Navigator, lease), and `GameStateStore` (cross-task observed game
  facts). A task can outlive an attempt and a session can host many tasks.
- A pause preserves the task definition, lifecycle, progress, and serialized
  checkpoint; it need not retain raw screenshots or a live executor object. On
  resume, the Processor reconstructs an execution view and the Navigator returns
  to the checkpoint's safe anchor. This preserves semantics without an
  unbounded in-memory context.
- Business output has two explicit routes: progress/checkpoint/result goes to
  Processor, which owns lifecycle and external notifications; typed game
  observations go to `GameStateStore`, which owns cross-task facts. Immediate
  CV2/OCR results remain local to the consuming step. No general event bus is
  justified until multiple real consumers require fan-out.

## 2026-08-30 Entry and Processor Audit

- The current production HTTP path is still route-owned: `server/routes/task.py`
  builds closures around legacy runners and submits them to the module-global
  `TaskManager`; `/api/ops/*` has additional direct device-operation paths.
- `dispatch/Processor` currently has a useful queue/pause prototype but is not
  connected to production HTTP, timer, or CLI entry points. Its mutable
  `Request` and untyped parameter dictionary are transitional, not the final
  command contract.
- `scheduler/TaskScheduler` owns a second task list, trigger list, and execution
  loop. Keeping it as a peer runtime scheduler would preserve two competing
  task-state authorities.
- `server/task_manager.py` owns task lifecycle, stop signaling, worker threads,
  device lease use, and GUI notifications. This overlaps the planned Processor
  and is the main consolidation target.
- Top-level target: HTTP, timer, and CLI become thin adapters that validate
  transport shape, construct one immutable `Command`, and call the same
  Processor. System start/stop remains application-host/runtime lifecycle,
  outside task dispatch; device operations still require the runtime lease.

## 2026-08-30 Control Plane Compatibility Findings

- `python` and `uv` are process launch mechanisms, not business command formats;
  compatibility must translate parsed argv or public API arguments inside each
  explicitly supported legacy facade. A generic shell-string executor would be
  both unsafe and unable to reliably observe the original `uv` invocation.
- Current built-in combat plan YAML files contain combat payload only and omit
  the prototype dispatch `task_type`. New task YAML and legacy plan YAML must
  therefore meet at a normalization boundary before Processor admission, rather
  than forcing every Executor to parse both formats.
- `resolve_plan_path()` currently accepts a direct arbitrary existing path before
  checking `plan_root`; that behavior is useful for legacy scripts but cannot be
  the GUI task-file trust boundary. The new GUI path contract needs an allowed
  root check after canonicalization.
- `examples/auto_daily.py` represents runtime startup plus ongoing trigger
  policy, not one task. Its compatibility path needs a timer command producer
  rather than another task queue; the producer may live in GUI or backend.

## 2026-08-30 One-Shot Task and Validation Clarification

- The user confirmed the business boundary: one YAML submission produces one
  finite task instance; repeated/idle execution is implemented by submitting
  additional instances from a trigger.
- `RuntimeHost`/`RuntimeControl` are explanatory names for system startup/stop,
  not additional public entry layers or mandatory message infrastructure. After
  conversion, the request is an ordinary AutoWSGR task order handled by
  Processor.
- YAML admission should distinguish file/path, syntax/schema, task-field, and
  business-combination validation. Runtime conditions (device/page/fleet
  availability) are execution outcomes, not malformed YAML.
- GUI status continuity requires an in-memory authoritative task record plus
  WebSocket updates and HTTP snapshot queries. Disk persistence across backend
  restarts is a separate later feature; no database is justified for the first
  vertical slice.
- A timer/idle trigger may live in GUI, backend, or a legacy compatibility script;
  its only contract is to submit one finite task at each firing. Whether it must
  continue while the GUI is closed is a product decision, not a Processor layer.

## 2026-08-30 Entry Contract Corrections

- The YAML execution-count field is intentionally removed. CLI/API carry a
  `count`/`repeat_count`, and Processor expands it into finite one-shot queue
  items. This preserves the one-task execution boundary while supporting a
  repeated request.
- The repeat expansion still needs product semantics for per-item failure,
  stop scope, and GUI aggregation. These are not implementation details because
  they change what the user sees as one operation.
- Pause is resumable with the runtime alive; stop is cooperative cancellation
  that returns home; interrupt is forced runtime teardown that clears context
  regardless of the current step. The latter cannot promise a final GUI status.
- Current YAML fields remain the compatibility baseline; no mandatory
  `schema_version`/`task_type` addition is required in the first slice. If the
  GUI sends only a path, the task kind must come from the endpoint, CLI command,
  or an unambiguous directory convention.
- Priority is a shared policy: GUI may arrange/display insertion according to
  it, while Processor validates and enforces the final queue order. Request
  idempotency is intentionally deferred for the local single-machine topology.
- The CLI live status display is a recorded future feature, not a reason to add
  a terminal UI dependency now.

## 2026-08-30 Macro Questions After User Corrections

- The remaining Processor blockers are business choices, not layer design:
  whether `count` returns one aggregate batch or N visible task items, how the
  unchanged YAML identifies its business type, what failure/stop do to remaining
  repeats, and whether GUI queue intent or Processor queue state is authoritative.
- Immediate backend teardown after a forced GUI close requires a process-ownership
  guarantee (GUI supervises the backend) or a future heartbeat. HTTP alone cannot
  observe a killed peer process.
- A forced interruption must not reuse stale task context on the next start;
  startup must reconcile the emulator to a known home page before accepting work.

## 2026-08-30 Final Business Constraints for the First Slice

## 2026-08-30 Exercise Implementation Review

- The current branch has a working first adapter from YAML HTTP requests to
  `Processor`, and the focused server/E2E tests pass with an isolated writable
  pytest basetemp.
- `Request` currently assigns priorities 60..10 even though the agreed public
  priority scale is limited to 10; the policy must use a bounded scale while
  preserving the relative order.
- `Request.__post_init__` assumes string/integer inputs before validating their
  types. Admission errors should be deliberate `ValueError`s rather than
  incidental `AttributeError`/`TypeError` exceptions.
- `extre` is parsed but the YAML HTTP adapter always calls `submit()`. The
  current `TaskManager` single-worker gate also rejects a second request, so
  insertion cannot yet be a real behavior. The first slice can keep the queue
  local to one Processor, but must not claim that an external insertion was
  honored when no Processor is alive to receive it.
- CLI cleanup reaches into `Launcher._ctrl`; use the public launcher/context
  lifecycle to avoid coupling the new entry point to a private field.

- The GUI sends a YAML path and a requested execution count. The backend owns
  execution and returns completed-count information; GUI calculates its own
  display denominator and keeps its own queue presentation.
- `task_type` is a YAML field written by GUI generation. The backend validates it
  against the task-specific schema and does not infer business from arbitrary
  filenames or executor guesses.
- Failure handling is progressive: a recoverable error may soft-retry, then a
  hard retry may close/reinitialize through the SL path before retrying. A
  non-recoverable failure ends the task with failure evidence.
- GUI stop preserves remaining requested count for GUI policy; CLI stops the
  current finite run. Hang-up/daily plans remain trigger producers that submit
  ordinary one-shot tasks.
- Current GUI/backend queues are intentionally not merged in this slice. The
  backend recognizes `extre` as insertion intent, while later integration will
  align queue snapshots and priority behavior.
- GUI X and CLI Ctrl+C are process-level termination paths. A restart discards
  runtime context, runs initialization, detects home, and uses SL reinitialization
  when the emulator is not already at home.

## 2026-08-30 Exercise Slice Final Findings

- The first Sakuya vertical slice now has one normalized `Request` path from
  YAML to `Processor`, with bounded priorities, finite `count`, immutable
  top-level parameters, cooperative pause/stop, progressive retry, and flat
  GUI-compatible result details.
- The HTTP adapter preserves the existing `TaskManager` response/status shape;
  it does not yet provide insertion across two independently created HTTP
  processors. That remains an intentional integration boundary for the next
  slice.
- E2E cases always attempt home-page cleanup and public launcher disconnect;
  abnormal game exits are detected at action/check boundaries and trigger one
  reinitialization attempt. Existing screenshot/OCR tools were reused.
- No GUI source, visual behavior, or frontend contract files were modified.
- Full-suite residual risk is limited to the pre-existing repair-test import
  mismatch and the unexecuted real-device path; both are recorded rather than
  masked with compatibility code.

## 2026-08-30 Complete Exercise Migration Start

- The controlling reference is `architecture-upgrade-minutes.md` in this meta
  worktree; all implementation choices must remain inside its replacement-mode
  and single-owner boundaries.
- A new isolated task worktree was created from the completed exercise slice:
  `.worktrees/20260830-sakuya-exercise-migration-8d3f`.
- Real-device E2E is explicitly deferred until static validation is complete;
  five attempts are reserved and will be numbered in `progress.md`.

## Static Inventory: Exercise Chain

- The current exercise executor is a flat `business/combat/exercise.py` file.
  It already routes through `Processor`, but still imports the legacy
  `ui.battle`, `business.system.navigate`, `ops.startup`, and `GameContext`
  directly; it only accepts `fleet_id` and does not consume YAML fleet rules.
- The map page and exercise panel have already been physically moved to
  `infra/base/ui/pages/map`; the exercise panel supports five rivals, top/bottom
  scrolling, challenge-state pixel checks, and the opponent-info-to-preparation
  transition. Its remaining direct preparation-page import is the next seam.
- `combat/fleet.py` already contains the canonical immutable `ShipSelector`,
  `FleetSlotRule`, `FleetPreset`, and YAML/API conversion helpers. Normal sortie
  uses them through `resolve_fleet_selection` and `BattlePreparationPage.change_fleet`.
- The tested fleet algorithm in `ui/battle/fleet_change` already implements
  primary/fallback assignment, strict/relaxed type and level checks, OCR retry,
  duplicate prevention, slot alignment, and final verification. Reusing it is
  lower risk than writing a second exercise-specific selector.
- `CombatEngine` already models exercise as a single-point mode, defaults to
  the night-battle decision supplied by `CombatPlan`, recognizes the result,
  clicks through settlement, and returns to `EXERCISE_PAGE`.
- The GUI's checked-in exercise YAML currently contains only `task_type`,
  `fleet_id`, and legacy `times`; the requested per-slot rules therefore need
  a documented `fleet_presets`/`ships` shape in the backend fixture or user
  YAML, without changing GUI source in this task.
- HTTP still wraps a newly-created `Processor` inside the module-global
  `TaskManager` worker. This is not a single shared Processor and cannot honor
  cross-request insertion; it is an explicit integration boundary to address
  minimally for the exercise route rather than claim as complete.
- The first migration pass moved the battle-preparation/chooser implementation
  and low-level interaction helpers into `infra/base/ui`; legacy `ui` paths are
  module aliases so existing consumers and patch-based tests resolve to the
  same implementation. Combat's event-map template lookup was made lazy to
  keep direct infra imports acyclic.
- Static regression after that pass is clean for the moved surface: `337 passed`
  across battle preparation, chooser, ship-list, navigation, normal-fight, and
  combat tests. The old patch targets resolve to the same implementation module.
- The new executor now parses an immutable exercise plan from YAML-compatible
  params, applies the normal sortie fleet selector, defaults the combat plan to
  single-column night battle, reports formation/battle checkpoints, and always
  attempts a home-page cleanup. Its focused static tests currently cover the
  main path and a pause at ship selection.
- Processor priority direction is now aligned with the minutes: smaller numbers
  are higher priority (`expedition_check=0` through ordinary/event sorties=5),
  and its executor-event bridge can request a pause when a higher-priority item
  is waiting at a safe exercise checkpoint.
- Full static pytest after the current implementation reports `1064 passed,
  4 failed`: three known baseline imports of removed `autowsgr.ops.repair`, and
  one compatibility assertion fixed by omitting the new `expected_names`
  keyword for built-in ship names. No new behavioral failure remains in that
  run; the suite will be rerun after the remaining edits.
- The legacy repair import is now a thin module alias to
  `business/logistics/repair/bath_repair`; the repair regression is green
  without creating a second implementation.
- The E2E exercise case now supports both `expedition_check` and
  `reward_check` insertion and its relay sequence covers the five requested
  handoff nodes (`panel_ready`, `formation_entered`, `ship_selected`,
  `before_start`, `rival_done`).
- Full pytest after adding the repair facade and Processor/route handoff logic
  is green: `1069 passed`. The task-specific OCR candidate path is covered by a
  focused ship-list test and does not change calls for built-in names.
- Targeted Ruff for the new dispatch, exercise, route, fleet-model, and E2E
  files is clean. The moved legacy page files still contain their pre-existing
  complexity/style findings; they are kept as-is except for import-boundary
  edits and are tracked separately from this slice's new code.
- Device preflight is read-only and healthy: `adbutils` sees `emulator-5554`,
  `com.huanmeng.zhanjian2` is running (pid 2689), screenshot is 1280x720, and
  page recognition reports `主页面`. No click, navigation, or E2E attempt has
  been spent.

## Real E2E Attempt 1 (failed before battle)

- Initialization, FastOCR, map entry, opponent 1 selection, and the first four
  fleet replacements succeeded on the real device.
- The requested `S-198` and `S189` searches returned zero DLL rows on all three
  OCR passes; slot 5 and the candidate-only slot 6 remained empty, so the
  executor correctly refused to start an invalid fleet. This is a real account
  data/ship-list availability issue, not a silent fallback.
- Failure cleanup exposed a separate deterministic navigation defect: while the
  preparation page was visible, the global page registry falsely identified it
  as `活动页面`; `goto_page(HOME)` then entered the activity-page close loop.
  The process was stopped after preserving logs/screenshots, and the game was
  reinitialized to `主页面`.
- Attempt budget is now `1/5`; no second attempt will run until both the input
  plan and cleanup false-positive are addressed statically.

## Static Follow-up After Attempt 1

- The false `活动页面` match is deterministic: the event overlay template
  `fight_button_20260730_540p.png` is searched over the full screen and matches
  the preparation-page `出征准备` title at `(0.13, 0.05)` with `0.870`
  confidence. The real event control is a lower-right control, so its matcher
  must be constrained to that physical region.
- `BATTLE_PREP` intentionally is not in the global navigation registry. Thus
  removing the false match alone would leave cleanup unable to route from a
  preparation page. The exercise executor must first use its existing
  `BattlePreparationPage.go_back()` transition, then invoke normal navigation
  from the map page.
- The final fleet-failure logger currently emits an exhaustion error for every
  assigned ship, including slots that already match. It must report only the
  slots that remain unmatched or lack required strict validation.
- The account state captured in attempt 1 has no selectable `S-198`, `S189`,
  `阿尔汉格尔斯克`, or `水貂` rows after three OCR/DLL passes. The first four
  requested ships are real and selectable. The six-slot fixture therefore cannot
  reach battle on this account without changing the test input; the fixture must
  remain unchanged, and any later full-path smoke must use an explicitly recorded
  account-valid YAML override.
- Attempt 2 with the four-ship account-valid override passed end to end. The
  existing fleet was recognized as already satisfying the target, so no
  replacement clicks were issued; battle, night choice, settlement, count,
  home cleanup, and disconnect were all verified.
- Attempt 3 established an account/game constraint: a ship already assigned to
  another fleet can appear as an OCR-matched selectable row, but clicking it
  leaves the destination fleet unchanged. The final position OCR catches this
  and fails closed, so the executor does not start an invalid battle. The same
  cross-fleet target must not be used again in a real attempt.
- Attempt 4 passed the real `panel_ready` handoff: expedition priority paused
  the exercise, four expeditions were collected, and the same request resumed
  and completed a battle with its count intact. The home-anchor cleanup path is
  stable under an actual interrupt.
- Attempt 5 passed the real `before_start` handoff: reward priority paused the
  preparation page, one pending task reward was collected, and the exercise
  resumed and completed opponent 3. All five real-device attempts are now
  exhausted; no further device validation should be performed in this slice.

## 2026-08-31 Campaign Migration

- The old campaign implementation was concentrated in `ops/campaign.py` and
  mixed name parsing, map navigation, preparation, and combat execution.
- The new vertical path is `Request` → `Processor` → `CampaignExecutor` →
  `CampaignOperations` → application UI pages/common interaction →
  `business.combat.run_combat`.
- `CampaignSpec` freezes campaign name/difficulty, battle plan, repair/night/
  formation defaults, and one canonical fleet selection before device work.
- Campaign repeat count now belongs to `Request.count`; one executor run emits
  one `CombatResult`. Terminal `BATTLE_TIMES_EXCEED` and `DOCK_FULL` results
  stop the current batch through a Processor event.
- Campaign calibration values now come from common `colors`, `ocr`, and
  `coordinates` resources. The page layer remains responsible for physical
  coordinates and difficulty detection.
- Direct `CampaignRequest` validation now maps unknown campaign names to HTTP
  422 before a task is started. Ambiguous or oversized fleet definitions fail
  during campaign admission instead of being silently truncated.
- Static verification passed: campaign/dispatch/server focus 67 tests,
  adjacent combat/map/preparation/scheduler/server focus 415 tests, full
  pytest 1094 tests, targeted pre-commit, compileall, diff check, and `uv build`.
- No real-device campaign E2E was run; this slice is intentionally static.

## 2026-08-31 Campaign Fleet Rules

- The generic preparation-page algorithm removes extra ships with logical-slot
  compaction and uses `_circular_move`/`swipe` to reorder; that behavior is
  incompatible with campaign formation.
- `CampaignFleetChangeMixin` now intercepts only `task_type='campaign'` and
  reuses the existing OCR/chooser primitives while replacing each physical
  slot directly. Empty slots stay empty at their original index.
- Hard campaign rules are encoded in `CAMPAIGN_FLEET_TYPES`: destroyer is six
  destroyers; cruiser is BB/CA/CA/CL/CL/DD; battleship is BC/BB/CA/CA/DD/DD;
  carrier is CV/CV/DD/DD/DD/DD; submarine is three SS.
- Explicit hard-campaign fleet names receive the fixed per-slot type rule and
  exact required count. Without names, the preparation page validates the
  current OCR type/occupancy snapshot and fails closed when it does not match.
- Simple campaigns retain unrestricted fleet input and permit one slot.
- Exercise now passes `task_type='exercise'` through the same public page
  method and continues to use the generic algorithm.
- Targeted verification passed: campaign pytest 22, exercise pytest 13,
  Ruff check/format and targeted pre-commit. Full pytest was intentionally
  skipped per user instruction.

## 2026-09-01 Campaign Contract Audit

- The corrected campaign taskbook is the acceptance source for this batch;
  GUI team-name path resolution remains a final-integration TODO.
- The navigation graph previously had `BATTLE_PREP -> MAP -> HOME`, so a pause at
  a fleet checkpoint can safely leave the preparation page through the shared
  navigation service.
- Campaign-specific fleet changes are point-to-point. The inherited preparation,
  fleet, and OCR logs now use English module prefixes (`[Fleet]`/`[OCR]`).
- Campaign progress currently records a checkpoint marker, but the executor
  always cleans up to `HOME`; continuous campaign reuse must be decided at the
  Processor handoff boundary rather than hidden in the page operations.
- `ops/campaign.py` only needs to remain a legacy import facade; the support
  implementation is already owned by `application.combat.support`.
- Taskbook wording says the business layer reads and validates YAML, while the
  architecture minutes assign YAML admission to `TaskDefinitionLoader` and
  `Processor`. This batch keeps one owner in the minutes' direction: request
  admission loads/validates, and `CampaignSpec` freezes business parameters;
  no second YAML loader is introduced.

## 2026-09-01 Campaign E2E Findings

- The first campaign run stopped before battle because the migrated
  `ChooseShipPage` signature was still calibrated to the old 960x540 layout.
  The failure screenshot showed the real `选择舰船` page; updating the shared
  normalized signature made it match 5/5 on the captured 1280x720 frame.
- One simple campaign run then completed after clearing and refilling slot 1;
  the battle engine needed one existing soft retry before a successful result.
- `panel_ready` + expedition, `formation_entered` + reward,
  `fleet_checkpoint` + expedition, `before_start` + reward, and `battle_done`
  + expedition all completed with pause-home-resume assertions passing.
- The two-round device run completed both battles, but it occurred before the
  final reuse-marker lifecycle fix and therefore still initialized home between
  rounds. The final reuse behavior is covered statically; no campaign attempts
  remain today to re-run it.
- Hard campaign fixed-slot type/count behavior and the supplied six-slot strict
  fleet are statically covered only; no device asset was available after the
  daily campaign quota was consumed.

## 2026-09-04 Decisive Smoke Findings

- `testing/ops/decisive_battle.py` referenced a removed public `serial` field
  and passed a removed `ocr` constructor keyword; both were test-tool drift.
- OCR-enabled `launch_for_test` skipped `ensure_ready`, so a previous map or
  overlay could violate the required home-page starting state.
- `ops/startup.py` still imported the deleted `ops.navigate` module.
- The decisive map template points to the overview menu, not the in-map page;
  `SIG_MAP_PAGE` correctly matches the 1280x720 in-map screenshot.
- The Ex-1 fleet-overlay correction was missing its chapter guard and caused
  Ex-6 recovery maps to enter `CHOOSE_FLEET` incorrectly.
- A real Ex-6 smoke reached the unified decisive fleet branch and completed the
  first node. The second node could not be completed with the available
  battle-fleet state; this is recorded as a partial smoke, not a full clear.

## 2026-09-04 Decisive Business Migration Findings

- The repository's established business packages register executors lazily
  through `dispatch.registry`; `decisive` now follows that path.
- The old controller is a multi-stage state machine, so the first migration
  keeps its internal helper classes together and adds a thin `BaseExecutor`
  entry. This preserves behavior while leaving checkpoint ownership for the
  next business-refinement slice.
- HTTP decisive requests now use `Request.count` for repeated full-chapter
  executions; `DecisiveConfig.decisive_rounds` is not passed into the business
  definition.
- `ops/decisive` has no production implementation left. A dynamic
  `ops.destroy` call remains only for the unrelated full-dock recovery branch.

## 2026-09-04 Top-Level Governance Findings

- `infra` is mostly compatibility aliases. Its only substantial runtime state is
  `infra/runtime/context`, which belongs under `application/runtime`.
- `application` and `common` already contain the canonical combat, UI, device,
  vision and system implementations; the top-level `infra` copies are not
  independent owners.
- Top-level `ui` is a legacy compatibility namespace around
  `application/ui`, while top-level `ops` still contains unmigrated business
  implementations and facades. They must be handled differently.
- `scheduler` mixes runtime startup with queue/trigger logic. Startup belongs to
  `application/runtime`; queue and timer policy belong to `dispatch`.
- `constants` and `contracts` contain dependency-free shared values and can be
  moved into `common` with mechanical import updates. `types.py` is a shared
  module rather than an extra top-level folder and will be handled separately.

## 2026-09-05 First Coarse Layer Governance

- The backend worktree contains only `server`, `dispatch`, `business`,
  `application`, and `common` as top-level architecture packages; `__pycache__`
  is ignored generated output.
- The initial registry used business-side `register()` calls, which made the
  lower business layer mutate the higher dispatch layer during import. The
  registry now owns explicit `(module, class)` mappings and loads classes lazily.
- `BaseExecutor` previously imported pause/stop exceptions from
  `dispatch.processor`. Those exceptions now live in `common/contracts/task.py`,
  so the business layer no longer points upward.
- `business/navigation` was only a forwarding module. Removing it makes
  `application/ui/navigation` the single Navigator entry without changing
  navigation behavior.
- The architecture regression test now checks both the root package set and
  import direction. It passed together with the focused feature suite.

## 2026-09-05 Business Domain Split

- `business/legacy_ops` mixed combat runners, port operations, compatibility
  exports, and documentation. It was not a valid third business domain.
- Production business now has only `combat` and `logistics`; ordinary and event
  sortie share `combat/bettle`, while build/cook/destroy join logistics.
- Task initialization had no business-domain ownership, so its package moved to
  `application/runtime/initialize` and callers now use that canonical path.
- The campaign compatibility runner is colocated at
  `business/combat/campaign/compat.py` rather than hidden in a cross-domain
  bucket.
- A route test still patched the removed `autowsgr.ops` facade; it now patches
  the concrete bettle module imported by the route. The affected suite passed.

## 2026-09-05 Combat Shared Fleet Flattening

- `business/combat/fleet/model.py` combined immutable selection models with
  native/YAML/API conversion; its package `__init__.py` only re-exported names.
  A single `business/combat/fleet.py` keeps the combat shared boundary visible
  without an unnecessary package level.
- `FleetPolicy` includes normal, exercise, campaign, decisive, and expedition
  modes, so its canonical cross-domain location is `business/fleet_policy.py`.
- The public import path `autowsgr.business.combat.fleet` remains unchanged
  after flattening, avoiding caller churn.
- The final focused suite passed `585` tests, including architecture and fleet
  preparation regressions.

## 2026-09-05 Shared Combat Boundary

- `business/combat/handlers.py` mixed generic phase execution with combat
  decisions. Generic phase dispatch, result-page progression, and terminal page
  actions now live in `application/combat/engine/phase_handlers.py`.
- Business handlers retain plan-driven enemy/formation decisions, SL policy,
  node progress, and business result interpretation.
- `CombatHistory`, `CombatResult`, and event records are shared output
  capabilities and now live in `application/combat/history.py`; business keeps
  only a compatibility re-export.
- `BaseExecutor` adapts Processor control signals to safe waits and events, so
  it now lives in `application/runtime/executor.py` rather than business.
- Final focused verification passed `604` tests; targeted pre-commit and
  compileall passed.

## 2026-09-05 Handler and Runner Follow-up

- `business/combat/handlers.py` still combines node decisions, result
  interpretation, and the application phase mixin. The split can preserve the
  existing MRO with `decision`, `settlement`, and a package `__init__`.
- `business/combat/engine.py` is only an adapter that combines business hooks
  with `application.combat.engine.CombatEngine`; it should be named
  `runner.py` so the application engine remains the only engine owner.
- Existing production callers use `run_combat` through the combat package;
  tests patch the old module paths and need canonical module updates.

- The first focused pytest invocation hit a permissions error while pytest
  scanned the shared system temp directory; rerunning with an explicit
  worktree-local `--basetemp` passed all tests.
- Ruff was not installed as a standalone `.venv` executable; the repository
  pre-commit Ruff hook ran successfully and fixed two import-order issues on
  its first pass.

## 2026-09-05 Bettle Unified Entry

- `business/combat/bettle/normal_fight.py` already contains the shared page,
  preparation, combat, and result flow; `_is_event` currently derives from
  `plan.chapter`.
- `event_fight.py` is only a compatibility subclass and convenience wrapper;
  no business `BaseExecutor` exists for either `normal_fight` or `event_fight`.
- The Processor registry can point both task types at one class. Passing the
  task type through `BaseExecutor` keeps the mode decision explicit without
  duplicating the battle flow.

- `BettleExecutor` now parses the loaded plan once, initializes the home
  anchor, injects the base wait hook into `NormalFightRunner`, reports
  `battle_done`, and returns home after a normal completion.
- Legacy `normal_fight` and `event_fight` functions remain available, while
  new Processor requests resolve to the unified executor.

## 2026-09-05 Remove UI Compatibility Layer

- `application/ui/legacy` contains compatibility aliases/re-exports, not a
  second page implementation. Its root `__init__.py` also duplicates page
  registration and old aggregate exports.
- Remaining production imports are in startup, bettle, logistics build/cook/
  destroy, and `server/routes/game.py`; tests/tools/examples use the old paths
  extensively and must be redirected before deletion.
- Canonical targets are `application.ui.pages.*`,
  `application.ui.navigation.*`, `common.ui.interaction`, and
  `application.ui.ship_list`.

- Removing `legacy` also exposed two old aggregate imports: map constants now
  come directly from `pages.map.data`, and interaction waits come directly
  from `common.ui.interaction`.
- The canonical UI source count is now 70 files (root contracts, navigation,
  and pages); the 45-file legacy tree is gone.

## 2026-09-05 Navigation Service Split

- `service.py` now owns only the public retry wrapper `goto_page()` and the
  step-by-step navigation loop `_goto_page()`.
- `recognition.py` owns screenshot retries, page registry lookup, recognition
  constants, and `ctx.current_page` synchronization.
- `navigation/__init__.py` still exports `goto_page` and
  `identify_current_page`, so external callers do not change.

## 2026-09-05 Navigation Ownership Cleanup

- Current `registry.py` mixes page registration with screenshot recognition and
  re-exports eight low-level interaction helpers solely for compatibility.
- Current `stack.py.resync()` performs page recognition, so the state object
  depends on the registry. The intended split is recognition-driven reset plus
  state-only stack operations.
- `graph.py` contains public, combat, and logistics edges in one file; its
  existing imports can remain stable through a `graph/` package facade.
- The canonical split is now in place: `service.py` exposes only `goto_page`
  and `_goto_page`; E2E tools use `recognition.py`; pytest-only graph, registry,
  and stack objects remain available without entering the business path.
- Navigation regression and architecture tests passed (`48 passed`), targeted
  pre-commit passed, and `compileall` plus `git diff --check` passed.

## 2026-09-05 Navigation Governance Audit

- The real navigation chain is `goto_page -> _goto_page ->
  identify_current_page -> register_default_pages -> page checker ->
  UIStack.observe -> graph.find_path -> UIStack.push -> NavEdge.action`.
- Graph actions only select a page controller. The controller performs the
  page click, waits for the target checker, and returns the stable page to the
  navigation loop.
- Navigation core directly uses `common.types.PageName`,
  `common.vision.page_match.PageMatch`, `common.system.logger`, and
  `common.ui.interaction.NavigationError`; `ctx.ctrl.screenshot()` and
  `ctx.ctrl.click()` arrive through the runtime controller contract.
- Page actions transitively use `common.ui.interaction` waits/clicks,
  `common.vision` matchers/OCR/templates, `common.calibration` coordinates and
  signatures, `common.system` logging/exceptions, and `common.types` values.
- `business` still has a few direct common UI imports: `destroy.py` uses
  `click_and_wait_for_page`, `bettle/normal_fight.py`, campaign operations,
  and exercise operations use `NavigationError`, and combat decision handlers
  use `wait_leave_page` plus vision matchers. These are boundary candidates,
  not navigation-core dependencies.

## 2026-09-05 Navigation and UI Boundary Review

- Navigation owns cross-page movement: page recognition, route lookup, stack
  reconciliation, edge execution, and stable arrival at a business entry.
- `application/ui/pages` owns page-level behavior: coordinate clicks, page
  state recognition, waits, panel transitions, and page-specific validation.
  Graph callbacks call these semantic page methods rather than common helpers.
- `common.ui.interaction`, `common.vision`, `common.calibration`,
  `common.device`, `common.system`, and `common.types` have consumers beyond
  navigation. They remain common; moving them to application would invert the
  dependency boundary and duplicate wrappers.
- `common.ui.interaction` does contain navigation-specific residue: a second
  `NavigationError`, unused `candidates`/`handle_overlays` parameters, and
  legacy wording around `confirm_operation`. These are follow-up cleanup items,
  not reasons to add a new facade in this slice.
- Business code should call `goto_page` plus semantic page/application methods.
  Direct business imports of common UI primitives are boundary leaks to remove
  only when each caller has a real page-level operation to own.
- `application/ui/pages` already is the application UI entry for business.
  Do not add an `application/ui/operations.py` pass-through module; it would
  only duplicate page methods. Add a new application method only when a real
  multi-page UI workflow needs one owner.

## 2026-09-06 UI Controller Reorganization Baseline

- The bound backend worktree is `codex/20260830-sakuya-exercise-consolidated-7a6c`.
  Existing user changes are the nine deleted feature reports and remain untouched.
- `application/ui/pages` contains 61 Python files: standalone page controllers,
  page packages, shared fleet/ship/tabbed capabilities, data/recognition modules,
  and explicit compatibility shells.
- Production, tests, tools, and examples contain approximately 400 references to
  `autowsgr.application.ui.pages`; the package move must update all of them together.
- Navigation behavior is frozen for this task. Only page import paths may change
  as a consequence of the move.
- `tabbed_page.py` and `choose_ship.py` are shared UI capabilities and belong
  under `controller/shared`, not `common`. `battle_preparation/fleet_change/`
  is reused by several combat flows but stays with the battle-preparation
  Controller because it composes that page's base and detection mixins; moving
  it to `shared` creates a circular import through `battle_preparation.__init__`.
- `common` already owns screenshots, clicks, waits, OCR, image matching,
  templates, calibration, logging, and device access. Move code there only when
  it has no page semantics.
- No `application.ui.pages` forwarding package is planned; all real consumers
  must move to the canonical `controller` path.

### Ponytail audit follow-up

- `shared/tabbed_page.py` needed `Path(__file__).resolve().parents[4]` after the
  move; `parents[3]` resolved to `autowsgr/application` and broke template
  loading. The corrected path was verified by loading all five templates.
- `map/data.py` had a dead `CLICK_PANEL` mapping with no callers; it was
  removed along with its unused calibration import.
- `common/vision/map.py` had a stale `int` annotation and compared `None` with
  an integer for denominator-only OCR. The return type and guard now match the
  actual result contract, with a focused regression test.
- `decisive/legacy_fleet_change.py` remains a live production algorithm and was
  not deleted as a compatibility shim; its caller and tests still use it.

## 2026-09-06 UI Calibration Downshift Baseline

- Remaining Controller constants fall into three groups: physical calibration
  (coordinates, probes, crop regions, colors, tolerances, pixel signatures),
  visual algorithm tuning (card geometry, OCR scale and scan thresholds), and
  page/workflow semantics (enums, state tables, retry and timeout policy).
- Physical calibration should be grouped in existing domain calibration modules
  backed by `common/data/calibration`, not copied into a global constants file.
- Page/workflow semantics must stay in Controller because common cannot import
  Controller enums or own page state. Controller may map its enums to stable
  calibration keys at the boundary.
- Clear remaining calibration owners include `bath_page/signatures.py`,
  `build_page.py`, `canteen_page.py`, `friend_page.py`, `intensify_page.py`,
  `sidebar_page.py`, `event/event_page.py`, `mission_page/data.py`, and the
  decisive page/overlay modules.
- `battle_preparation/base.py` already consumes common calibration but still
  owns page enums and computed maps; those maps must only move when their keys
  no longer depend on Controller types.
- Existing common calibration YAML does not yet have dedicated bath, build,
  canteen, friend, intensify, sidebar, event, or decisive files. Adding a
  domain file is justified only when it contains real values; no one-line
  wrapper modules are needed.

## 2026-09-06 UI Calibration Downshift Audit

- The architecture minutes require UI calibration to live in read-only,
  page-organized data resources; a flat Python constants file is not the final
  shape. The current uncommitted `common/calibration/ui.py` therefore needs to
  be replaced by page-domain accessors backed by the existing coordinates,
  colors, OCR, and signature loaders.
- Remaining controller-owned calibration includes sortie sidebar swipe/fallback
  probes, choose-ship scrolling, mission list scrolling, canteen fallback
  clicks, decisive map crop and return/settlement clicks, plus event templates.
  Retry counts, sleep policy, page enums, workflow maps, and business parsing
  rules remain in the Controller layer.
- `decisive/map_controller.py` still has a stale `reward_ack_pos` reference
  after the local constant was moved; the common reward coordinate must be used
  on both reward-popup branches.

## 2026-09-06 Worktree Preservation

- The original nested `AutoWSGR` worktree remains untouched as the source copy.
- A canonical paired `meta` and `AutoWSGR` worktree now exists under the project
  `.worktrees` directory with the shared task branch
  `codex/20260830-sakuya-exercise-consolidated-7a6c`.
- The tracked diff and the untracked `bath_page/constants.py` were migrated to
  the new backend worktree; source and target status outputs match.
- An obsolete duplicate `meta` worktree admin record was quarantined after
  confirming that the active worktree points to the newly created record.

## 2026-09-07 BathPage Review Confirmation

- The user verified in the game that the repair list is always ordered by
  repair duration descending, with the longest item on the far left.
- `BathPage.repair_longest()` therefore intentionally stops at the first page
  containing an eligible ship; no global cross-page selection algorithm is
  needed under the current game contract.
- The remaining broad per-card exception concern is separate and remains
  unresolved for a later decision.

## 2026-09-07 UI Controller Sample Baseline

- `[规范]navigation-code-style.md` requires file-level caller/dependency
  docstrings, business-based sections, grouped action prefixes, Google-style
  function contracts, and comments for rules and failure boundaries.
- `build_page`, `backyard_page`, and `canteen_page` currently have no OCR logic;
  page recognition belongs in `page.py`, so an empty `recognition.py` would add
  no value.
- Their page-specific coordinate wrappers are only consumed by the target page
  modules. `build_page` also reaches into `ShipType.relative_position_in_destroy`,
  which is a build-page coordinate that must move with the build constants.
- The target sample shape is therefore `__init__.py` + `constants.py` +
  `page.py` for these three non-OCR pages, with `recognition.py` reserved for a
  module that actually owns OCR rules.

## 2026-09-07 UI Controller Module Standard

- Added `[规范]ui-controller-code-style.md` based on the navigation comment
  standard and the effective BathPage boundaries.
- The standard uses absolute imports, `check_` for state predicates,
  `read_` for visible state, action-specific prefixes for UI operations, and
  business-flow ordering rather than alphabetic function ordering.
- Page-specific coordinates must be private normalized `0.xxxx` constants with
  business-semantic comments. OCR-only code belongs in `recognition.py`; pages
  without OCR do not get empty recognition files.
- Build-page ship-type filter coordinates currently live on `ShipType` and are
  part of the build constants migration boundary.

## 2026-09-07 Build Page Rewrite

- `build_page` now owns its normalized page, slot, destroy-filter, and animation
  coordinates in `application/ui/controller/build_page/constants.py`.
- The page package exports `BuildPage` and `BuildTab` through `__init__.py`;
  page recognition is `check_current_page`, visible tab state is
  `read_active_tab`, and destroy actions use `click_`, `open_`, or `confirm_`
  prefixes.
- The page-specific `ShipType.relative_position_in_destroy` property and the
  obsolete build calibration wrapper/YAML were removed after consumer search
  found no other callers.
- Build has no OCR-owned logic, so no empty `recognition.py` was created.

## 2026-09-07 Backyard Page Rewrite

- `backyard_page` now owns its normalized return and subpage navigation
  coordinates in `application/ui/controller/backyard_page/constants.py`.
- The package exports `BackyardPage` and `BackyardTarget`; the page predicate is
  `check_current_page`, and child-page imports use absolute paths.
- The old backyard calibration wrapper/YAML had no consumers outside the target
  page and were removed. No OCR logic exists, so no recognition file was added.

## 2026-09-07 Canteen Page Rewrite

- `canteen_page` now owns normalized page, recipe, popup, and animation
  coordinates in `application/ui/controller/canteen_page/constants.py`.
- The package exports `CanteenPage`; its page predicate is
  `check_current_page`, and the animation action is `click_skip_animation`.
- The old canteen calibration wrapper/YAML had no remaining consumers and were
  removed. No OCR logic exists, so no recognition file was added.

## 2026-09-07 UI Controller Rewrite Complete

- The three target pages now use package directories with private constants and
  page executors. Since none owns OCR rules, each intentionally omits an empty
  `recognition.py`.
- Build-specific coordinates were removed from `ShipType`; all target page
  callers were updated to the unified `check_current_page` predicate.
- The old single-file page modules and their page-specific calibration wrappers
  and coordinate YAMLs were removed after consumer scans found no other users.

## 2026-09-07 Ponytail Audit

- The requested package boundaries and private constants are justified by real
  callers; no speculative Manager, Factory, compatibility alias, dependency, or
  empty OCR module was added.
- Duplicate page-local coordinates are intentional: the UI standard requires
  page calibration ownership to remain private rather than reintroducing a
  common coordinate source.
- No new context or OCR issue was found in the three non-OCR target pages; the
  existing issues remain in the two `[todo]` ledgers.
- Remaining non-OCR risks for the report are the unavailable runtime dependencies
  (`cv2`, `yaml`, and Ruff), unverified external consumers of renamed methods, and
  the lack of emulator/device verification in this environment.

## 2026-09-07 Comprehensive Report

- Added `[报告]ui-controller样板重构综合报告.md` with the complete scope,
  implementation summary, Ponytail audit, TODO ledgers, validation evidence,
  and remaining risks for morning review.
- The report explicitly distinguishes pre-existing Bath/Exercise changes from
  this task and does not claim unavailable runtime or test checks passed.
