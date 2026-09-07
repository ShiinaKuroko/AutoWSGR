# Findings & Decisions

## Requirements

- 将 Backyard、Bath、Canteen 三个 Controller 归入 `controller/backyard/`。
- 采用 `main_page`、`bath_page`、`canteen_page` 三个同级页面包。
- 保持 BathPage 内部业务实现不变，只迁移路径并更新调用方。
- 保留当前未提交的后院坐标常量改名和食堂 `close_popup` 改名。

## Findings

- 当前目标 worktree：`C:\ShiinaKuroko\01.Project\AutoWSGR\.worktrees\20260830-autowsgr-upgrade`。
- 当前绑定根覆盖整个目标目录及其 `meta` 子目录。
- 现有包为 `backyard_page/`、`bath_page/`、`canteen_page/`。
- 直接消费者包括 navigation graph、navigation registry、logistics business、main page controller 和 UI tests。
- `bath_page` 拥有 `constants.py`、`page.py`、`recognition.py`；其他两个页面没有 OCR 专属逻辑。
- `main_page` 已被母港控制器使用，因此新目录必须通过 `backyard/main_page` 的完整路径区分。
- 三个页面已移动为 `backyard/main_page`、`backyard/bath_page`、`backyard/canteen_page`；三个页面包保持各自的 `constants.py`、`page.py`，Bath 继续保留 `recognition.py`。
- 生产、导航、业务、测试和 E2E 说明中的完整 Controller 导入路径已更新；测试目录名和页面变量名未改动。
- `backyard/__init__.py` 只承担领域目录说明，不聚合导入子页面，以保留原有延迟导入并避免循环依赖。
- 关键 Python 文件 AST 解析和 `compileall` 均通过；旧完整 Controller 导入路径无残留。
- 运行时 Controller import smoke 被当前环境缺少 `pydantic` 阻塞，未通过安装依赖绕过；这不改变静态路径验证结果。

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| 物理目录按业务域归组，三个页面包同级 | 反映页面边界，不把子页面误建模为主页面实现细节。 |
| 使用现有包级导出模式 | 减少导入改动和循环依赖风险。 |
| 延迟导入策略保持不变 | Backyard、Bath、Canteen 存在互相返回/导航关系，避免新增导入环。 |

## Issues

- 主仓库之外的旧 worktree 不作为本次写入目标。

## Sidebar Reorganization

- 侧边栏业务域由原 `sidebar_page.py`、`friend_page.py`、`intensify_page.py` 和 `build_page/` 组成。
- `build_page/` 已是页面包，包含建造与拆解标签；它应作为 `sidebar/` 下的同级页面包整体移动。
- `friend_page.py` 和 `intensify_page.py` 当前是单文件，将各自包装为仅含 `__init__.py` 与 `page.py` 的页面包，不制造空的 OCR 或常量文件。
- 现有侧边栏、好友、强化、建造页面之间存在回退/导航导入；移动时保留延迟导入，避免导入环。
- 侧边栏四个页面已移动为 `sidebar/main_page`、`sidebar/friend_page`、`sidebar/intensify_page`、`sidebar/build_page`；`build_page` 继续承载建造和拆解标签。
- 新侧边栏完整导入路径扫描无旧路径残留，42 个关键 Python 文件 AST 解析和 `compileall` 通过。
- 新路径运行时导入 smoke 在既有校准加载阶段因环境缺少 `yaml` 失败；未安装新依赖或修改校准逻辑。

## Sidebar Style Rewrite

- `sidebar/main_page/page.py` 当前从 `common.calibration.sidebar` 读取关闭、导航、二级菜单坐标，并在页面文件内保存 `SUBMENU_DELAY`。
- `sidebar/friend_page/page.py` 当前从 `common.calibration.friend` 读取返回坐标。
- `sidebar/intensify_page/page.py` 当前从 `common.calibration.intensify` 读取返回和标签坐标。
- `common.calibration.sidebar/friend/intensify` 及对应三个坐标 YAML 只有上述页面消费者，满足删除公共包装并下沉页面常量的条件。
- `SidebarPage.is_current_page`、`FriendPage.is_current_page` 和 `IntensifyPage.is_current_page` 需要统一为 `check_current_page`；`IntensifyPage.get_active_tab` 需要统一为 `read_active_tab`。
- 四个页面均无页面专属 OCR 规则；不新增 `recognition.py`。
- `build_page` 已有页面私有 `constants.py`，本阶段不改变其建造/拆解业务算法。

## Sidebar Style Rewrite Result

- `sidebar/main_page/constants.py`、`sidebar/friend_page/constants.py` 和
  `sidebar/intensify_page/constants.py` 现在分别拥有页面专属坐标与等待参数。
- 页面检查统一为 `check_current_page`，强化状态读取统一为 `read_active_tab`，标签选择统一为 `select_tab`。
- 四个页面类的函数顺序按 `__init__`、检查/读取、页面动作、组合动作和页面边动作整理；私有二级菜单辅助位于文件末尾。
- 三个公共校准包装与坐标 YAML 已删除，未发现剩余消费者。
- 最终未创建任何 sidebar 页面 `recognition.py`；Bath 页面 OCR 实现未改动。

## Legacy Rule Compatibility Patch

- User explicitly requested manual transplantation of the compatibility behavior from `c5a464c`; `c5a464c` will not be cherry-picked or merged because this worktree has a different architecture and extensive local changes.
- `_parse_legacy_condition()` currently strips only outer whitespace before splitting; its uppercase regex rejects lowercase ship codes and operators written as `> =` or `! =`.
- `autowsgr.server.schemas.NodeDecisionRequest` already routes legacy enemy rules through this parser, so no Schema source change is needed.
- The normalization must preserve `AP = 1` as invalid while accepting `AP == 1`.

## Remaining UI Controller Boundary Audit

- `map/` is the map page root: `MapPage` is assembled through multiple panel mixins in `map/panels/`; its MRO and shared state make it a high-risk last-stage refactor.
- `battle_preparation/` is a reusable combat page group consumed by normal, exercise, campaign, and decisive flows; its `fleet_change/` subtree contains campaign/decisive-specific selection policy but operates on the shared preparation page.
- `decisive/` is a self-contained page group with overview, decisive map, decisive preparation, overlay detection, and fleet OCR; it should not be nested under `map/` without first resolving the separate `DecisiveMapController` boundary.
- `event/` currently contains one large event-map controller with template selection, difficulty, overlay, entrance, and navigation behavior; it is an independent page group.
- `mission_page/` is already a package with page, data, and recognition modules; it is the lowest-risk next candidate for style/ownership normalization.
- Recommended implementation order: `mission_page` → `event` → `decisive` → `map` → `battle_preparation`.
- Shared `common.calibration` consumers must be audited per page before any constants are moved; no remaining Controller files are moved during this audit phase.

## Home Page Rewrite Scope

- The physical target is the actual home/port page, so its canonical Controller domain is `home_page`, not `main_page`.
- `PageName.MAIN` remains the stable navigation state; only UI Controller package and class names are candidates for renaming.
- Existing `overlays.py` and `event_nav.py` have real consumers in runtime initialization and the home controller; they are not dead files to delete for the sake of a three-file template.

## Home Page Rewrite Result

- `controller/main_page/` was moved to `controller/home_page/`; `controller.py` was renamed
  to `page.py`, and the Controller class is now `HomePage`.
- `HomePage.check_current_page`, `check_base_page`, `check_task_ready`,
  `check_expedition_ready`, and `read_overlay` follow the page naming convention.
  Existing `PageName.MAIN`, `Templates.MainPage`, and test directory names remain stable.
- `home_page/constants.py` now owns the normalized page coordinates, notification color,
  and the two pixel signatures actually used by the page. `Target` is a page navigation
  type and `OverlayKind` is an overlay module type, so neither remains in `constants.py`.
- `main.yaml`, `colors/main.yaml`, and `signatures/main.yaml` were retained for the generic
  calibration API and its tests; the Controller no longer reads those files through
  `common.calibration`.
- Production, navigation, business, testing, tools, and direct documentation references
  were synchronized. The remaining `MainPage` matches are visual-resource compatibility
  names, not Controller imports.
- No `recognition.py` was created because the home page has no page-specific OCR rules.

## Home Page Directory Naming

- `HomePage` follows the existing Controller class convention used by `MapPage`,
  `MissionPage`, `BackyardPage`, and `SidebarPage`: business name plus `Page`.
- The final package path is `application/ui/controller/home/`; only the directory
  changed from `home_page`. The package files and public class did not change.

## Home State Naming

- `PageName.HOME` is now the only enum member for the value “主页面”; the serialized
  value remains unchanged for recognition, navigation logs, and external strings.
- All production, navigation, business, test, tool, and documentation references were
  synchronized. `Templates.MainPage` and template resource member names remain untouched.

## Mode-Specific Bath Navigation

- The handoff source worktree uses the older `autowsgr/ops` and `autowsgr/ui` layout;
  its behavior was manually adapted to `application/ui/navigation/service.py` and
  `application/ui/navigation/__init__.py`. No source worktree was modified.
- `goto_bath_from_normal_sortie` first calls `BattlePreparationPage.go_back`, then
  delegates to the existing map → HOME → backyard → bath route.
- `goto_bath_from_decisive_sortie` returns to the decisive map, opens the exit dialog,
  calls `confirm_leave` (never `confirm_retreat`), verifies `DecisiveBattlePage`, then
  delegates to the existing bath route.
- The generic `BATTLE_PREP -> MAP` graph edge was removed because the preparation page
  parent is mode-dependent. Activity preparation return remains an explicit TODO.

## Semantic Page Navigation Names

- `go_home_page` means navigating to the actual mother-port page represented by
  `PageName.HOME`.
- `HomePage.go_to_backyard` means entering the backyard, and
  `HomePage.go_to_sidebar` means entering the sidebar.
- `HomePage.Target.BACKYARD` now maps to `PageName.BACKYARD`; the previous
  `Target.HOME` name incorrectly described that destination.
- The runtime helper names `is_on_home_page`, `recover_to_home_or_restart`,
  `_is_on_home_page`, and `_wait_for_home_page` were synchronized with the same
  terminology. Existing public behavior and serialized page values are unchanged.

## Manual Bath Repair Termination

- `ShiinaKuroko` latest merge is `cce7121`, with `7443018` as the second parent;
  `7443018` is based on `450c88a`, which is based on `e6d9fee`.
- The source implementation introduces `ManualRepairRequiredError` as a terminal
  signal, dispatches detected target ships by name in the bath, updates runtime
  ship/bath state, and returns home in cleanup.
- The source scheduler and API handlers stop the whole task after this signal;
  remaining rounds must not be consumed.
- The upgraded architecture has no `autowsgr/ops` or `autowsgr/ui` packages, so
  each source entry point must be manually mapped to `common/system`,
  `application/ui`, `business`, and `application/runtime` equivalents.
- Campaign preparation is a separate business operation and must pass a
  campaign-specific bath navigation callback while preserving target slot names.
