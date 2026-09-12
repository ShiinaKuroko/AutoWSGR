# Findings & Decisions

## Requirements

- 将 Backyard、Bath、Canteen 三个 Controller 归入 `controller/backyard/`。
- 采用 `main_page`、`bath_page`、`canteen_page` 三个同级页面包。
- 保持 BathPage 内部业务实现不变，只迁移路径并更新调用方。
- 保留当前未提交的后院坐标常量改名和食堂 `close_popup` 改名。

## Findings

## Shared Top Tabs Ownership

- top_tabs 同时被 battle_page、build_page、intensify_page、friend_page 和 mission_page
  使用，属于 shared UI 能力，不应归入 sortie_page。
- shared/tabbed_page.py 已重命名为 shared/top_tabs.py，保留 TabbedPageType、
  check_tabbed_page、get_active_tab_index、make_tab_checker 等既有 API。
- 这是顶部标签识别/校验能力，不是具体页面；MAP、BUILD、INTENSIFY、MISSION 和 FRIEND
  页面继续由各自 Controller 注册和调用。

## Battle Page Map Governance

- map 是五个顶部标签 Mixin 的聚合 UI Controller，不应整体放入 navigation；导航器只
  注册 MAP、维护导航边，并调用 battle_page 的公开页面动作。
- 最终页面包为 operations/sortie_page/battle_page，保留 base.py 作为 Mixin 公共基类，
  page.py 作为 MapPage 聚合器，constants.py 作为聚合页校准，data.py 作为面板/章节数据。
- 地图标题 MapIdentity、文本解析和截图 OCR 已收拢到 recognition.py；BaseMapPage 只
  通过 read_map 委托识别入口。
- 地图页面专用校准已从混合旧入口收敛到 battle_page/constants.py；演习、战役和远征
  专用常量继续由各自子页面所有，旧 common.calibration.map 保留兼容。
- 旧 controller/map 当前导入已全部同步，MapPage 的五个 Mixin MRO 和既有导航行为保持。

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

- `controller/home/main_page/` was moved to `controller/home/main_page_page/`; `controller.py` was renamed
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
- The final package path is `application/ui/controller/home/main_page/`; only the directory
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

## 2026-09-08 Sortie UI Governance Baseline

- `battle_preparation/` 是可复用的出征准备页面组，公开组合类为
  `BattlePreparationPage`，由 `BaseBattlePreparation`、检测、补给、维修和
  `fleet_change/` 多重继承组成；直接消费者包括普通出征、战役、演习、决战、
  支援和快速维修业务，以及对应 UI/业务测试。
- `battle_preparation/fleet_change/` 不是纯业务规则：`_selection.py` 会打开并等待
  `ChooseShipPage`，读取 `ctx.ocr`，点击出征准备页槽位，并由
  `campaign.py`、`decisive.py` 和 `_change.py` 编排模式差异。因此本批不下沉到
  `common`，也不移动用户重点维护的选船实现。
- `decisive/` 是独立页面组，包含决战总览、决战地图、决战准备、浮层识别和决战
  舰队 OCR；`DecisiveMapController` 同时被决战业务状态机和澡堂导航调用，暂不
  将其并入 `map/`。
- `event/` 当前只有一个活动地图控制器，职责包含活动标题/按钮模板识别、节点详情
  浮层、难度和入口切换；活动出征返回路线仍由导航层 TODO 约束。
- `map/` 是由 `BaseMapPage` 与五个面板 Mixin 组合成的地图页面组。地图面板分别
  负责普通出征、战役、决战、演习和远征；普通出征准备页的父页面不能恢复成无
  来源的通用 `BATTLE_PREP -> MAP` 边。
- `home/event_nav.py` 是母港到活动地图的专用导航动作，只由 `home/page.py`
  委托，不属于活动页面 Controller。
- `common.calibration.battle_preparation`、`decisive`、`event`、`map` 仍被多个
  生产模块、公共视觉代码或测试/工具直接使用；本阶段先不删除共享校准包装，先
  按页面逐项核对真实消费者。
- 目标域普遍仍使用 `is_current_page`、`get_*`、`has_*`、`recognize_*` 等旧命名，
  且若干文件存在装饰性分隔线、旧式参数文档或缺少完整文件级说明；这些是后续
  S1-S5 的结构治理项，不改变业务算法。

## 2026-09-08 Sortie UI Governance S6

- 统一审查确认目标页面组的状态入口已无旧的 `MapPage`、`BaseEventPage`、
  `DecisiveBattlePage` 和 `BattlePreparationPage` 状态命名遗留；shared/mission/start
  页面仍保留各自旧入口，未被本批误改。
- 新增的四个 `constants.py` 均与原 `common.calibration` 计算结果完成 parity；旧
  calibration 文件因测试、工具或共享视觉代码消费者暂留，不能直接删除。
- 选船子包的 `has_unknown_details` 和决战浮层的无调用方读取函数属于后续 ponytail
  删除候选，但本批不改变用户重点维护的选船实现或潜在外部入口。
- `bath_page` 未出现在本批 diff；活动出征手动维修和全部上下文/OCR问题均已记录
  到对应 `[todo]` 台账。

## 2026-09-08 Operations Aggregation

- 首页右下角任务、船坞、出征属于同一个同级功能区域，命名为 `operations`；当前
  只迁移已有的 `mission_page`，船坞页面尚未实现，不创建空页面包。
- `operations` 只作为目录归属包，不自动从包根重导出 `MissionPage`，与现有
  `backyard`/`sidebar` 避免跨页面导入副作用的约定一致；稳定入口为
  `application.ui.controller.operations.mission_page`。
- 任务页原有 `page.py`、`data.py` 和 `recognition.py` 均完整保留；迁移只改变包路径，
  `MissionPage`、`MissionPanel`、`ButtonType`、`MissionInfo` 和 `PageName.MISSION`
  行为不变。
- 迁移后发现 `mission_page/data.py` 存在重复的 shared calibration 导入和本地重载；
  已删除重复导入并让 `CLICK_BACK` 由任务页面数据模块直接定义，避免隐式导出在 lint
  修正后消失。

## PageName Semantic Naming Audit

- 当前 `PageName` 共 15 个成员：`HOME`、`MAP`、`BATTLE_PREP`、`SIDEBAR`、
  `MISSION`、`BACKYARD`、`BATH`、`CANTEEN`、`CHOOSE_REPAIR`、`BUILD`、
  `INTENSIFY`、`FRIEND`、`DECISIVE_BATTLE`、`CHOOSE_SHIP`、`EVENT_MAP`。
- 已确认 `PageName.HOME` 是主页状态，序列化值为“主页面”；之前的 `MAIN` 已完成替换，
  不应恢复。`Templates.MainPage`、`CommonPage` 和测试目录名不是本次 PageName 改名对象。
- 页面状态命名整体使用业务名，但存在四处风格不一致：`BATTLE_PREP` 使用缩写，
  `DECISIVE_BATTLE` 和 `EVENT_MAP` 混用页面后缀，`CHOOSE_SHIP` 使用动作短语。
- `PageName.CHOOSE_REPAIR` 在仓内没有任何成员调用方；实际识别对象是 `Bath` 下的
  “选择修理”浮层，且 `BathPage.check_current_page` 仍返回 `PageName.BATH`。
  它不能在未确认外部兼容性前直接删除或改成页面状态。
- 建议候选映射（只改 Python 成员名，不改枚举值）：
  `BATTLE_PREP -> BATTLE_PREPARATION`、`DECISIVE_BATTLE -> DECISIVE`、
  `EVENT_MAP -> EVENT`、`CHOOSE_SHIP -> SHIP_SELECTION`。
  `HOME`、`MAP`、`SIDEBAR`、`MISSION`、`BACKYARD`、`BATH`、`CANTEEN`、
  `BUILD`、`INTENSIFY`、`FRIEND` 暂无必要改名。
- 尚未执行上述改名，等待用户确认成员名映射；确认后需要同步注册表、导航图、业务、测试、
  工具和文档，并验证 `PageName(value)`、页面注册键和导航图序列化值不变。

## Mission Page Module Split

- `operations/mission_page/data.py` 原先同时保存页面标签、页面派生变量、物理校准、
  OCR 规则、任务结果模型和任务库读取，职责边界不符合当前 UI Controller 样板。
- 页面侧的 `MissionPanel`、`PANEL_LIST` 和 `CLICK_PANEL` 已移入 `page.py`；任务页面
  坐标、颜色、扫描阈值和滚动参数已移入 `constants.py`。
- OCR 结果模型 `ButtonType`、`MissionInfo`、任务库读取和任务识别已收敛到
  `recognition.py`；`recognition.py` 不执行设备点击或页面导航。
- 删除 `data.py` 后，包级导出仍提供 `MissionPage`、`MissionPanel`、`ButtonType` 和
  `MissionInfo`；现有生产调用方仍从 `operations.mission_page` 导入。
- 迁移后的任务库路径使用 `recognition.py` 的当前目录层级定位到
  `autowsgr/common/data/missions.yaml`，并通过 import smoke 实际读取验证。
- 旧 `meta` 参考文档中的 `mission_page/data.py` 属于历史架构记录，本次没有改写历史证据；
  当前生产、测试和工具代码没有残留该导入路径。
- 后续复核发现 `constants.py` 若继续导入 `common.calibration` 只是搬运加载逻辑，不能算
  页面常量私有化；现已改为静态坐标、颜色、阈值和滚动值。识别模块只在运行时把本页元组
  转成 `Color`/`ROI`，旧公共校准文件暂保留但不再是任务页依赖。

## Sortie Page Aggregation and Partial Governance

- 原 `application.ui.controller.operations.sortie_page.battle_page.panels/` 正好包含五个顶部标签模块：`sortie.py`、
  `exercise.py`、`campaign.py`、`expedition.py` 和 `decisive.py`；已整体迁移到
  `application.ui.controller.operations.sortie_page/`。
- `sortie.py` 和 `decisive.py` 本轮只做物理迁移，没有改实现、行为、导航契约或函数内容。
- `exercise.py`、`campaign.py` 和 `expedition.py` 已按两份规范整理文件级说明、业务分区、
  状态检查命名、公开 docstring 和函数顺序；演习滚动、战役难度/次数、远征收取算法保持不变。
- `MapPage` 仍通过五个 Mixin 组成完整地图控制器；`map/__init__.py` 对 `MapPage` 使用惰性
  导出，解决从 `sortie_page` 子模块直接导入时的循环，同时保留 `from ...map import MapPage`。
- 现有地图校准仍由 `map/constants.py` 提供，未在本轮把五个模块的校准重复搬迁；后续第二轮
  可在明确所有权后再处理，避免影响普通出征和决战的仅迁移边界。
- 旧 `map.panels` 路径在当前生产、测试、工具和文档代码中无残留；历史记录不做机械改写。

## Sortie Submodule Template Split

- `sortie_page/exercise.py`、`campaign.py` 和 `expedition.py` 已分别升级为
  `exercise_page/`、`campaign_page/` 和 `expedition_page/`。
- `exercise_page/` 与 `expedition_page/` 各包含 `__init__.py`、`constants.py` 和
  `page.py`；当前没有真实 OCR 规则，因此没有创建空的 `recognition.py`。
- `campaign_page/` 包含 `__init__.py`、`constants.py`、`page.py` 和 `recognition.py`；
  战役次数、舰船/战利品获取数量 OCR 及 `AcquisitionCounts` 已归入 recognition。
- 三个 constants 文件使用静态页面校准值；页面代码在 UI 边界内将 RGB 元组转换为
  `Color`，不再依赖旧 `map.constants` 的对应专属条目。
- `CampaignPanelMixin` 保留 `AcquisitionCounts` 类属性兼容入口；演习/战役/远征的
  既有公共方法和 `MapPage` Mixin 组合不变。
- 普通出征 `sortie.py` 与地图决战入口 `decisive.py` 没有纳入本轮治理，仍只发生文件迁移。
- `map/constants.py` 中的旧演习/战役/远征专属条目暂保，作为可能的外部兼容面；新目录已
  无当前代码依赖这些条目，后续可单独审计删除。

## Event Page Governance Scope

- 活动坐标由设备控制器以 int(relative * resolution) 截断；四位小数常量需取能保留
  1280x720 基准像素的位置，不能直接做普通四舍五入，否则可能产生 1 像素点击漂移。

- 活动页面只有模板匹配、像素状态读取和页面动作，没有 OCR 文本规则；按规范不创建
  空的 `recognition.py`。
- 原 `event/constants.py` 曾通过 `common.calibration` 动态加载页面校准；治理后已把
  活动专用坐标、颜色和 ROI 固化到 `event_page/constants.py`，保留旧公共校准文件作为
  兼容面，避免页面 Controller 继续依赖共享校准入口。
- `event_nav.py` 是跨页导航动作，不属于活动页面执行器；现已迁移为
  `application.ui.navigation.event`，由导航图中的 `HOME -> EVENT_MAP` 边和
  `HomePage` 共用，并删除未使用的 `is_base_page` 参数。

## Event Page Governance Result

- 活动页面 Controller 通常由首页活动入口进入，因此 `application/ui/controller/event/`
  已治理为 `application/ui/controller/home/event_page/`，与首页页面组的业务层级一致。
- 新目录保留 `__init__.py`、`constants.py` 和 `page.py`；活动页面类名和页面行为不变。
- 跨页入口动作已治理为 `application/ui/navigation/event.py`，不与活动页面 Controller
  合并；导航图和 `HomePage` 共享同一实现。
- 生产、导航、业务、测试、工具和文档均已同步新路径；旧导入路径扫描无结果。
- 本次只调整目录边界和引用，不修改活动页面行为、活动手动维修 TODO 或 `bath_page`。

## Decisive Page Aggregation

- 原 `controller/decisive/` 是决战页面组，包含总览页、决战地图、浮层、舰队 OCR、
  旧编队入口和出征准备页；已整体迁移为
  `controller/operations/sortie_page/decisive_page/`。
- `operations/sortie_page/decisive.py` 是地图顶部标签 `DecisivePanelMixin`，属于
  另一层聚合入口，保留在原位置，仅更新其对决战总览页的导入。
- 决战包的公共导出仍是 `DecisiveBattlePage`、`DecisiveBattlePreparationPage` 和
  `DecisiveMapController`；迁移后由 `decisive_page/__init__.py` 保持同名导出。
- 旧路径命中均已定位为生产导入、测试/工具导入或模块职责说明；没有改名类、方法、
  PageName 或业务行为。

## 2026-09-09 Decisive Controller Second Governance

- 决战页面组已按页面职责整理为 `page.py`、`map_page.py`、`preparation_page.py`、
  `overlay.py`、`recognition.py` 和 `legacy_fleet_change.py`；包级导出保持稳定。
- `constants.py` 已脱离 `common.calibration` 动态加载，点击和识别坐标统一为四位
  归一化值，并保留 1280x720 基准像素 parity。
- 总览章节 OCR、节点 DLL 识别、战备舰队 OCR、技能舰船 OCR、选船列表 OCR 和结算
  掉落 OCR 均由 `recognition.py` 承担；页面执行器只负责 UI 操作和流程编排。
- 统一 `read_stage`、`read_chapter`、`read_decisive_phase`、`read_node`、
  `read_fleet_options` 和 `read_fleet` 等状态/结果读取入口；未改选船算法。
- 节点 DLL 的宽泛异常处理、共享选船匹配和上下文 OCR 生命周期继续留在 TODO，
  等待后续专题和大型决战升级移植时集中处理。

## 2026-09-09 Login Module Migration Complete

- 启动画面已迁移到 `application/ui/controller/login/`，结构为
  `__init__.py`、`constants.py`、`page.py`；没有 OCR 规则，不创建
  `recognition.py`。
- `StartScreenPage` 已统一为 `LoginPage`，`is_current_page` 已统一为
  `check_current_page`；生产调用方、初始化流程、架构文档和重试示例已同步，未保留
  没有真实消费者的旧别名。
- 页面专用点击坐标和像素签名已从 `common.calibration.start_screen` 下沉到
  `login/constants.py`；四位坐标映射到原 1280x720 像素，签名规则逐项 parity。
  旧 common 校准模块和 `login.yaml`/`start_screen.yaml` 资源暂保为外部兼容事实。
- 启动画面在游戏进入前出现，没有游戏内父页面，故不实现 `go_back`；跨页面进入和
  回退由运行时启动流程负责。

## 2026-09-09 Shared Method Inventory Round 1

- `controller/shared/` 当前只有 `top_tabs.py` 和 `choose_ship.py`。`top_tabs.py`
  是独立的顶部标签视觉匹配能力，已经属于公共区域；它不拥有具体页面状态或导航。
- `choose_ship.py` 不是纯选船算法：`ChooseShipPage` 同时负责选船页面 UI 操作、
  页面检查、键盘/搜索框处理、OCR 结果读取和舰种/等级约束校验，并持有注入的
  `GameContext`。它被 `battle_preparation/fleet_change` 直接调用，决战/战役差异
  由准备页编队分支编排，不能仅按“多处调用”复制或下沉到 `common`。
- `battle_preparation/` 的公共能力分布在页面基类、检测、补给、维修和
  `fleet_change` 子包；`operations/sortie_page/` 同时包含 battle 地图聚合器、五个
  顶部标签 Mixin、战役/演习/远征子页面和独立决战页面组。下一轮需要逐项追踪公开
  方法的全部生产、测试和工具消费者，再决定哪些属于 shared、common/vision 或原页面。

## 2026-09-09 Shared Method Inventory Round 2

- `top_tabs.py` 的实际消费者为侧边栏好友/强化/建造、任务页面和 battle 地图聚合器；
  它提供标签模板加载、页面类型识别、当前标签索引和 checker 工厂，已有独立公共
  出口，无需再包装一层。
- `ChooseShipPage` 的生产消费者只有 `battle_preparation/fleet_change` 的普通、
  战役和决战编队分支；测试还直接覆盖其舰名匹配。它依赖注入的 `GameContext`、
  `ctx.ocr`、选船页面坐标和舰船数据，当前公共区域已是最小可复用边界。
- `choose_ship.py` 仍直接依赖 `common.vision.ocr._fuzzy_match`，且页面 OCR、
  UI 操作和约束选择混在一个 Controller 中；这是 Stage 2 的 OCR/私有 API 风险，
  本阶段只记录，不在公共区域整合时重写用户重点维护的选船算法。

## 2026-09-09 Shared Method Inventory Round 3

- `BaseMapPage` 已是五种出征顶部标签共用的地图基类，负责 MAP 页面检查、当前面板
  读取、面板切换/确保、远征通知、章节侧栏状态和回到首页；它依赖地图专属
  `MapPanel`、坐标和导航语义，继续归属 `sortie_page/battle_page`，不复制到 shared。
- 普通出征的章节/节点导航与决战地图控制器的阶段、节点、浮层和决战回退流程没有
  相同契约；“普通地图操作”和“决战地图操作”属于同一业务域的不同页面执行器，
  跨页路径仍由 `application.ui.navigation` 负责，本轮不新增空泛地图导航包装。

## 2026-09-09 Shared Area Integration Result

- 公共区域最终保留两个职责明确的子模块：`shared/top_tabs.py` 提供顶部标签视觉
  匹配和 checker 工厂，`shared/choose_ship.py` 提供选船页面的搜索、OCR 卡片点击和
  单舰选择动作；两个模块均已用 `__all__` 声明稳定出口。
- 地图能力不新增 shared 包：`battle_page/base.py` 已持有五个顶部标签共用的
  `BaseMapPage`；普通出征 `SortiePanelMixin` 和决战 `DecisiveMapController` 的
  页面状态、坐标、浮层和回退目标不同，跨页导航继续由 `application.ui.navigation`
  管理。
- 智能选船不复制到 shared：`ChooseShipPage` 只负责选船页面 UI/视觉边界，
  `battle_preparation/fleet_change` 负责普通、战役、决战的编队规划、槽位调整和
  业务规则；战役固定槽位与决战不使用搜索框都属于模式差异。
- 重复名称审计未发现未知的同契约共享方法；建造/强化标签、各页面 `go_back`、
  `read_active_panel` 和 `change_fleet` 均绑定不同页面状态或终态，保留原页面所有权。
- 选船模块的 OCR 上下文生命周期和私有 `_fuzzy_match` 依赖继续留在阶段二 TODO；
  本阶段未修改选船算法、导航状态机或 `backyard/bath_page`。

## 2026-09-09 Phase 1 Complete

- 阶段一完成登录迁移、公共方法盘点/出口整理和最终复核；阶段报告为
  `meta/[报告]ui-controller公共区域与登录阶段一报告.md`。
- 本阶段实际代码变更限于 `controller/login/`、运行时引用、登录单元测试，以及
  `shared` 两个子模块的 `__all__`；没有新增地图/选船策略包装。
- 未决上下文、OCR 和私有 API 风险已同步到既有 TODO；阶段二再处理全量规范、导航
  回退和视觉边界治理。

## 2026-09-09 Stage 2 Controller Review Inventory

- 当前 `application/ui/controller` 的 Python 文件均已有文件级 docstring；本轮重点
  转为函数命名/顺序、页面专属常量格式、公共出口和私有对象导入。
- 重复入口扫描发现旧式 `is_current_page` 仍存在于 `shared/choose_ship.py` 和
  `operations/mission_page/page.py`；`build_page`/`intensify_page` 的 `read_active_tab`
  和 `select_tab` 是各自标签集合，不是同一实现；`go_back`、`change_fleet`、
  `read_active_panel` 也因页面状态或终态不同不能机械合并。
- 方法顺序明显需要分批治理的文件包括 `battle_preparation/base.py`、
  `battle_preparation/repair.py`、`backyard/canteen_page/page.py`、
  `backyard/main_page/page.py`、`operations/mission_page/page.py`、
  `operations/sortie_page/sortie.py` 和 `decisive_page/map_page.py`；
  `bath_page/page.py` 保留为只审查不改行为的高风险边界。
- `shared/choose_ship.py`、`battle_preparation/fleet_change/_detect.py`、
  `top_tabs.py` 和若干旧页面仍直接依赖 `common.calibration` 或 OCR 私有对象；
  先确认每个导入对象后按“导入整个模块但不扩大私有 API”规则处理，OCR 匹配函数
  继续遵守既有 TODO 台账。
- 页面常量格式仍需逐模块核对，不能把枚举值、ROI 边界或业务数据误当点击坐标；
  既有四位归一化要求只适用于页面物理坐标，OCR/ROI 的所有权进入 2.3。

## 2026-09-09 Stage 2 Private Import and Ordering Review

- 直接导入 OCR 私有函数的 Controller 为 `backyard/bath_page/recognition.py`、
  `shared/choose_ship.py`、`battle_preparation/fleet_change/_detect.py` 和
  `operations/mission_page/recognition.py`；这些调用共享文本匹配/编辑距离实现，
  统一留待 2.3 OCR 专题处理，不在本批制造重复公共函数。
- 编队内部还有从私有模块直接导入 `_UnresolvedPrimaryError`、`_ShipSelection` 和
  `_MAX_SET_RETRIES` 的写法；它们属于同一编队子包的内部实现，可改为导入整个模块
  访问，保持私有可见性，不扩大稳定出口。
- `shared/top_tabs.py` 从 `common.calibration.tabbed` 导入的是公开校准常量，
  不属于“直接导入模块私有对象”；其页面类型和模板能力继续由 shared 所有。
- 方法顺序审计还发现 `canteen_page`、`backyard/main_page`、`battle_preparation`
  基类/维修/补给、`mission_page`、`battle_page/base.py`、普通出征 `sortie.py`
  和决战地图控制器存在分区顺序偏差；其中浴室页面只保留审查记录，不在本阶段
  改动既有业务实现。

## 2026-09-09 Stage 2 Coordinate Format Audit

- `home`、`backyard`、`sidebar` 和 `login` 的主要点击坐标已符合四位归一化格式；
  `battle_preparation`、`battle_page`、演习/战役/远征子页面和决战页面仍混有由
  1280x720 像素直接除法得到的长小数。
- 本阶段只格式化真实传给 `click`/`swipe` 的物理坐标，并逐文件验证四位值在
  1280x720 下仍映射到原像素；ROI 边界、颜色、OCR 参数和算法数据不按点击坐标处理。
- 坐标治理需要分批执行，先从 `battle_preparation/constants.py` 开始，再处理
  `sortie_page` 各子页面和决战常量，避免一次大补丁覆盖已有业务改动。

## 2026-09-09 Stage 2 Navigation Review Round 1

- 当前导航图由 `COMMON_EDGES`、`COMBAT_EDGES` 和 `LOGISTICS_EDGES` 组成：主页进入
  地图/任务/后院/侧边栏/活动，后院和侧边栏叶页面按页面控制器回退；普通地图和
  决战总览有明确的主页回退边。
- `BATTLE_PREP` 没有通用导航边是刻意约束：普通、决战和活动准备页的父页面不同，
  由显式业务路线或页面控制器处理，不能恢复无来源的 `BATTLE_PREP -> MAP`。
- 发现两个待确认的回退契约：`ChooseShipPage` 只有内部等待离开选船页的方法，
  没有独立 `go_back`；`DecisiveBattlePreparationPage` 与活动出征准备页继承普通
  `BaseBattlePreparation.go_back()`，可能把页面回退到普通 `MAP`，而不是各自真实父页。
- 登录页和主页属于流程根节点，没有游戏内父页面；决战地图控制器是非注册的内部
  页面组控制器，使用 `go_to_map_page` 处理准备页回退，不能直接等同普通 `go_back`。
- 以上属于导航兼容性评审结果；本轮不增加通用边、不改变状态机，待确认来源上下文
  后再决定是否给选船/模式准备页增加明确回退入口。

## 2026-09-09 Stage 2 Navigation Review Round 2

- `PageName` 继承 `StrEnum`，导航栈统一把页面状态归一为字符串；当前
  `find_path`、`UIStack.observe/push/candidates` 的字符串/枚举契约 smoke 通过。
- HOME 到后院/侧边栏/地图/任务/活动的入口和叶页面回退边均能在当前图中找到；
  普通出征到澡堂依赖显式 service 路线，决战到澡堂依赖决战专用控制器路线。
- 选船页虽注册了 `CHOOSE_SHIP`，但没有图边或独立 `go_back`；准备页回退目标依赖
  来源模式，当前普通基类实现不能代表决战/活动全部父页面。这两项保留为兼容评审项。
- 导航专项测试的 3 个失败是旧架构断言：误要求删除现有页面私有常量、拒绝显式
  澡堂导航函数、要求恢复无来源 `BATTLE_PREP -> MAP`；没有修改它们以迎合旧断言。

## 2026-09-09 Stage 2 Coordinate Format Batch

- `battle_preparation/constants.py` 的舰队、槽位、面板、支援、补给和血条点击/探测
  坐标已统一为四位归一化值，旧 1280x720 像素映射保持不变。
- `mission_page/constants.py` 的返回/标签坐标，以及战役和演习子页面的入口、探测、
  点击和滑动坐标已统一为四位值；与旧 `common.calibration` 的有效坐标逐项 parity。
- `battle_page/constants.py` 和 `decisive_page/constants.py` 的主要点击坐标已是
  四位格式；其余高精度值属于 OCR/ROI 裁剪边界，留待 2.3 视觉治理，不在本批改动。
- 所有修改均只涉及静态格式和值表示，未改变页面业务、选船算法、导航状态或浴室页面。

## 2026-09-09 Stage 2 Controller Governance Batch A

- 任务页状态检查、面板选择和任务读取入口已统一为 `check_current_page`、
  `select_panel`、`read_missions`、`read_all_missions`，所有当前调用方已同步；
  奖励动作和 `go_back` 按页面调用链后置，私有确认辅助放到文件末尾。
- 食堂页面的弹窗关闭动作已归入关闭分区，`go_back` 后置到做菜组合动作之后；没有
  改变做菜分支、确认/取消语义或坐标。
- 出征准备基类已将自动补给检查置于状态读取前，原子槽位/开关动作置于组合动作前，
  出征验证和页面回退后置；维修 Mixin 先检查、再执行槽位修理、最后执行组合修理。
- 编队私有对象改为模块访问，保持 `_UnresolvedPrimaryError`、`_ShipSelection` 和
  `_MAX_SET_RETRIES` 的私有边界；OCR 私有函数仍留待 2.3。

## 2026-09-09 Stage 2 Controller Governance Batch B

- `BaseMapPage` 已将远征通知检查放到读取入口之前；`DecisiveBattlePage` 已将总览
  原子动作、资源动作、章节组合导航和页面回退按调用职责排列。
- 任务页和食堂页的前缀/顺序治理已与导航注册和测试调用方同步；未改变页面业务流程。
- `battle_preparation.base` 已将状态检查、状态读取、页面原子动作、组合动作、回退
  和私有 OCR 选择属性分区；`repair.py` 检查入口先于修理动作。
- 本批未处理 `bath_page`、`shared/choose_ship.py` OCR 私有函数、决战地图复杂动作，
  也未改变选船算法；这些边界继续由 2.3/TODO 约束。

## 2026-09-09 Stage 2 Controller Governance Batch C

- `DetectionMixin` 已将舰队信息聚合入口放到血量检查之后、私有 OCR 辅助之前；
  `repair_action.py` 已按检查 → 槽位动作 → 重试组合排列。
- `BaseMapPage` 与 `DecisiveBattlePage` 的顺序治理保持通过；任务页/食堂页和准备页
  的前缀、分区、回退位置已完成同步。
- 仍待处理的结构项集中在 `sidebar/build_page`、`home/main_page`、普通出征 `sortie.py`
  和决战地图复杂动作；`bath_page`、选船 OCR 和页面坐标所有权按任务边界暂不扩散。

## 2026-09-09 Shared Area Task Login Discovery

- `controller/start_screen.py` 只有 `StartScreenPage.is_current_page()` 和
  `click_enter()` 两个页面入口；没有 OCR 文本规则，因此不创建空的
  `recognition.py`。
- 页面识别依赖 `signatures/start_screen.yaml` 的像素签名，点击依赖
  `common/calibration/start_screen.py` 的 `CLICK_ENTER`；原始 1280x720 像素
  坐标 `[1141, 618]` 对应归一化坐标 `(0.8915, 0.8584)`。
- 登录迁移目标为 `controller/login/__init__.py`、`constants.py`、`page.py`；
  `_CLICK_SETTLE = 2.0` 属于页面动作参数，保留在 `page.py`，不放入页面校准常量。
- 生产调用方是 `runtime/startup.py` 和 `runtime/initialize/initialize.py`；
  `docs/features/retry-plan.md`、`docs/architecture/ui.md` 仍有旧示例/说明引用，
  需要在迁移后同步。旧 `common/calibration/start_screen.py` 暂保为兼容入口。

## 2026-09-09 Stage 2 Review Complete for 2.1 and 2.2

- 2.1 完成 Controller 文件说明、非 OCR 私有导入、页面函数分区和主要点击坐标
  治理；OCR 私有函数、ROI 边界和上下文生命周期按 2.3 TODO 处理。
- 2.2 完成页面进入/回退矩阵、注册器、导航图和显式澡堂路线评审，报告为
  `meta/[报告]ui-controller导航兼容性评审报告.md`。
- 选船页缺少独立回退、决战/活动准备页共享普通回退是明确未决项；不添加无来源
  导航边，等待模式来源和上下文所有权确认。

## 2026-09-09 Stage 2 OCR/ROI Audit

- `common.vision.ROI` 已提供相对区域校验、像素裁剪和绝对坐标转换；
  `common.vision` 已提供 OCR 引擎和 `ship_list`/`combat` 等无页面语义视觉原语，
  当前没有需要重复迁移的新通用 ROI/OCR 实现。
- 页面专属 OCR 规则已经位于 `mission_page/recognition.py`、
  `campaign_page/recognition.py`、`battle_page/recognition.py`、
  `decisive_page/recognition.py` 和 `bath_page/recognition.py`；页面 `page.py`
  只负责截图、调用和页面动作。
- `battle_preparation/detection.py`、`battle_preparation/fleet_change/_detect.py`
  和 `shared/choose_ship.py` 仍把 OCR 读取、页面状态和编队算法耦合在 Controller 中；
  直接拆分会影响 Mixin/MRO、目标舰名分配和用户重点维护的选船行为，保留原实现，
  只处理私有函数导入形式。
- `Launcher.create_ocr()` 是通用 OCR 创建入口，`build_context()` 将其注入
  `GameContext.ocr`；`ship_ocr` 当前由同一启动器决定并注入。准备页、选船页和决战页
  对两者的优先级仍不一致，BathPage 仍会隐式创建 OCR，继续沿用上下文 TODO。
- `_fuzzy_match` 的 Controller 调用方已确认包括 shared 选船和准备页检测；Bath 与
  `common/vision/ship_list` 仍是其他调用方。`_edit_distance` 的任务 OCR 解析调用
  也属于同一私有 API 台账，不能只改一个消费者。

## 2026-09-09 Stage 3 Porting Audit Round 1

- `ShiinaKuroko` 最近两日时间线共 13 条记录：9 条业务/测试提交、2 条合并标记、
  1 个独立调试工具包和 1 个地图压力测试提交；合并标记不作为移植对象。
- `c5a464c` 的 `_parse_legacy_condition()` 大小写/组合运算符空格兼容已存在于目标
  `business/combat/rules.py`，对应解析器和 API 边界测试也已存在，初步判定无需重复移植。
- `e6d9fee` 的模式专用澡堂路线在目标 `application.ui.navigation.service` 已有普通、
  战役、决战架构化入口；仍需以源业务调用方逐项核对是否完整。
- `bc24d5e` 携带独立调试工具和 ADB 二进制，不属于当前业务运行时；除非发现当前目标
  缺少不可替代的功能，否则不移植。
- `cdc987e` 只有旧 E2E 压力测试场景，先评估断言价值，不迁移旧工具框架。

## 2026-09-09 Stage 2 Complete

- 阶段二完成 Controller 规范审计/治理、导航兼容评审和 OCR/ROI/上下文边界审计；
  2.1、2.2、2.3、2.4 均已在任务书勾选。
- 非 OCR 私有导入已改为模块访问，主要页面动作/读取/回退顺序和 click/swipe 坐标
  已治理并完成对应回归；任务页状态入口统一为 `check_current_page`。
- 没有重复迁移 `common.vision` 已有的 ROI/OCR 能力；选船 OCR 混合职责、BathPage
  隐式 OCR 创建、上下文优先级、DLL 宽泛异常和剩余私有 API 已写入 TODO。
- 导航报告为 `meta/[报告]ui-controller导航兼容性评审报告.md`；旧架构测试的
  3 个冲突断言保留为已知基线，没有回退来源区分设计。

## 2026-09-09 Stage 3 02ce4ed

- 源提交把“默认完整战果采集”落在两个默认值：`CombatPlan` 的兼容开关默认开启，
  `build_transitions()` 及 MAP/SINGLE 内部构图函数默认开启；显式 `False` 仍表示快速穿行。
- 当前新架构的结算处理器已经消费 `plan.collect_result_info`，因此不需要新增第三套
  结算状态或修改处理器；只同步状态图默认值和计划属性即可。
- `testing/combat/test_result_dismiss_unit.py` 已将测试辅助默认设为 `True`，并继续显式覆盖
  快速路径；本批不改它。

## 2026-09-09 Stage 3 02ce4ed Verified

- 默认值移植后，空 `CombatPlan` 的 `collect_result_info` 和默认 MAP/SINGLE 状态图均进入
  `EXP_SETTLEMENT`；显式 `collect_result_info=False` 的快速路径仍通过原有测试。
- 结算处理器无需改动，因为它本来就以 `plan.collect_result_info` 作为唯一分支条件；本批
  仅同步其上游默认值和契约测试。

## 2026-09-09 Stage 3 9b000b4 Verified

- 目标新架构没有旧提交中的 `ops.task_manager` 边界，维修方式契约落在现有
  `CombatPlan`/server serializer；澡堂等待状态落在现有 `server.task_manager`，保持一个
  任务状态所有者。
- `goto_bath_from_event_sortie` 是活动准备页唯一来源明确的回退路线，未恢复通用
  `BATTLE_PREP -> MAP` 边；活动地图到主页的既有 `EVENT_MAP -> HOME` 边继续复用。
- 全局 `repair_manually` 兼容路径在活动模式现在也能使用活动专用回退；显式
  `repair_method='bath'` 采用新等待语义，手动派修成功后重新进入原出征准备页。

## 2026-09-09 Stage 3 1d7fca7 Verified

- 目标地图代码原本把页面 OCR、章节切换策略和旧高亮探针混在 `sortie.py`/`base.py`；
  本次按现行 Controller 规范拆开，固定槽位坐标和 OCR 白名单属于 `battle_page` 私有校准。
- 章节选择只在目标槽位可识别、方向步长可证明时点击；占位符或当前状态不确定时等待并
  返回失败，不再用随机抖动坐标猜测。
- `MAP_NAV_SETTLE_DELAY` 同时作为章节/地图切换后的动画等待参数，替代普通出征章节
  动作继续依赖旧 `CHAPTER_NAV_DELAY` 的含义混用；旧高亮读取保留是为了当前 E2E 诊断，
  不作为导航路径。

## 2026-09-09 Stage 3 0577f15 Verified

- 决战入口点击和地图等待已经属于同一个 `DecisivePhaseHandlers` 状态转换；源提交的
  2 秒是首帧稳定窗口，直接复用现有 `WAITING_FOR_MAP` 截止时间和状态，不需要新状态源。
- 阶段三没有把 `ShiinaKuroko` 的旧 `ops`/`infra` 目录搬进目标；功能分别落在当前
  `business`、`application`、`server`、`dispatch` 和测试边界，排除项和已存在项均已写入台账。

## 2026-09-09 Strict Controller Rework Baseline

- 当前目标分支工作区干净，真实 Controller 文件树与旧报告不一致：顶层仍有
  `battle_preparation/` 页面组，`operations/sortie_page/` 仍有 `sortie.py` 和
  `decisive.py`，`home/main_page/` 仍有 `overlays.py`；这些路径需要按职责重新命名
  或归位，不能以“已迁移”代替治理。
- `battle_preparation/preparation.py` 是页面组合入口，却不是规范要求的 `page.py`；
  `shared/choose_ship.py` 是跨模式页面控制器，但仍混合 OCR、上下文和共享校准，按
  用户约束保留算法并把结构/视觉风险留在 TODO。
- 当前生产、测试和工具消费者已经逐项定位；结构批次需要同步路径，不保留没有真实
  消费者的兼容别名。浴室页面和选船算法不在本批次改动范围。
- 结构批次的命名决策：`battle_preparation` 归入
  `operations/sortie_page/battle_preparation_page`，其页面组合入口由 `preparation.py`
  改为 `page.py`；`sortie.py` 和 `decisive.py` 改为 `sortie_panel.py` 和
  `decisive_panel.py`，因为它们是顶部标签 Mixin；主页 `overlays.py` 改为
  `overlay.py`。这些是物理重命名和引用同步，不保留无消费者别名。
- `shared/choose_ship.py` 确认是跨模式页面控制器，包化为
  `shared/choose_ship_page/page.py` 但保留其现有选船算法、OCR 调用和共享校准依赖；
  不创建空 `recognition.py`，校准下沉和 OCR/上下文生命周期继续进入 TODO。
- 行为编排批次已将明确的 `is/get/ensure/switch` 状态或面板入口统一为
  `check/read/open/click/select` 语义；`start/enter/collect/change` 仅保留为有独立
  业务结果的组合动作，不把它们改成无意义的 `click_*` 包装。
- `BuildPage` 的解体过滤流程和 `ChooseShipPage` 的私有辅助已按实际调用链排序；除
  保护的 BathPage 外，模块级说明、私有导入和旧路径审计通过。

## 2026-09-09 Strict Controller Rework Final Verification

- 最终 focused 回归为 `364 passed`；controller、navigation、business 和 application
  相关目录 compileall、稳定入口 import smoke、目标文件 pre-commit 与 `git diff --check`
  全部通过。
- 当前 Controller 内没有旧文件名、旧路径或已治理的旧公共 API 名称残留；页面模块文件级
  说明审计通过，`backyard/bath_page` 没有进入 diff。
- 未执行真实游戏/模拟器 E2E；选船 OCR/上下文、决战节点视觉异常、BathPage OCR 和
  `PageName` 语义统一继续由既有 TODO/台账承接。

## 2026-09-09 Stage 4 Decisive Debug Audit

- 参考决战 debug worktree 的核心提交为 `7bd0ece`、`c55f994`、`9596446`；当前工作区
  仍有未提交的 staged entry polling、reset/fleet 标题门禁、浮层 ROI 和稳定性修正，
  所以只能作为候选实现参考。
- `9596446` 将决战地图事实从旧 `enemy_spec.yaml` 改为 18 个 `EX-x-y` 节点图文件，
  每个文件包含 branch-qualified node IDs、`next` 边、可达 key points 和敌方代码；
  目标当前仍使用 `common/data/map/decisive_battle/enemy_spec.yaml` 与硬编码查询。
- 目标当前运行时只保存基础节点字母，参考路线数据保存 `A1/A2` 等分支节点 ID；
  后续移植前必须决定是否扩展状态/API，不能用隐式的基础字母映射制造第二个路线游标。
- 参考未提交入口轮询移除了目标已验证的 `0577f15` 2 秒等待；后续应先保留当前等待，
  用时序测试证明新轮询等价后再评估调整。
- 已产出阶段四参考计划，明确资源路径映射、依赖顺序、冲突、验证门禁、回滚点和用户
  确认项；本阶段不修改任何决战代码或参考 worktree。

## 2026-09-09 Vertical Sortie Page Split

- 用户确认 `sortie_page/main_page` 承载 sortie 页面壳和顶部标签能力；
  `check_current_page` 的业务语义是“已进入 sortie_page”，不是普通出征地图识别。
- `sortie_page` 最终只保留 `main_page`、`battle_page`、`campaign_page`、
  `decisive_page`、`exercise_page` 和 `expedition_page` 六个页面目录；现有
  `sortie_panel.py`、`decisive_panel.py` 和聚合 `MapPage` 不再作为架构目标。
- 普通出征章节/地图定位、地图 OCR 确认、掉落/战果/舰船数量读取和进入出征准备归入
  `battle_page`；顶部标签读取/切换归入 `main_page`；各模式动作归入对应页面。
- 现有 `battle_preparation_page` 位于 `sortie_page` 下，与“只保留六个目录”的约束冲突，
  需要在结构盘点阶段确认迁移到 `operations` 直属页面组。

## 2026-09-10 Fleet Main Page Rework

- 当前 `fleet/main_page/page.py` 仍继承 `DetectionMixin`、`SupplyMixin`、`RepairMixin`、
  `CampaignFleetChangeMixin` 和空的 `BaseBattlePreparation`；`base.py` 已没有可复用的
  基类状态，因此页面继承只是在隐藏能力依赖。
- 准备页能力按 `preparation`（页面原子操作和页面状态）、`fleet_status`（舰队状态识别）、
  `supply`（补给/支援）和 `repair`（快速维修）拆分；识别实现进入各能力的
  `recognition.py`，校准值进入同目录 `constants.py`。
- `fleet_change` 核心算法内部仍依赖页面方法和 `_ctrl`/`_ctx`；用私有组合适配对象转发
  页面能力，保留算法和现有页面实例 patch 契约，不让 `BattlePreparationPage` 继承算法类。
- 最终结构为 `page.py` 加 `preparation`、`fleet_status`、`supply`、`repair`、
  `fleet_change`；旧 flat 能力文件已删除，准备页页面类基类仅为 `object`。
- 适配后的准备页/换船/业务回归为 `368 passed`；能力入口、消费者 smoke、compileall、
  目标 pre-commit 和 `git diff --check` 均通过。

## 2026-09-12 Fleet Rewrite Planning and Standards Audit

- Battle Page 的可复用样板是包级单一入口、页面主流程优先、识别实现私有和校准配置集中；
  不应机械要求每个小流程同时创建 `workflow.py` 与 `operations.py`。
- Fleet 重写目标确定为根主流程加 `main_page`、`formation`、`inspection`、`supply`、
  `repair`、`departure`、`shipyard_page` 子流程；旧兼容全部删除。
- 当前两份规范存在通用规则重复、基础规范命名错误、流程排序冲突、`as` 和坐标精度规则
  过宽、任务特例污染以及缺少包边界/状态/错误/机器门禁等问题。
- `navigation-code-style.md` 此前未进入 Meta `.gitignore` 白名单，其他 worktree 无法可靠取得；
  已将导航规范、新任务书和规范评审文档加入精确白名单。
- 仓库没有现成 Code Graph 工具；第一版可用标准库 AST 构建模块、符号、导入、调用、
  注册、配置、资源和测试关系，不依赖 `uv.lock` 中的传递依赖 `networkx`。

## 2026-09-12 Fleet Three-Boundary Architecture Correction

- 维护者否决根 `workflow.py` 加 `formation/inspection/supply/repair/departure` 平铺结构；
  Fleet 一级目录必须只表达三类职责：页面控制器、选船核心、辅助功能。
- 页面控制器负责编队/准备页面 UI 控制与对外主流程编排；它可以调用另外两类一级模块，
  但不得重新实现 OCR、规则规划、船池搜索、补给或维修细节。
- 选船核心必须按真实流程节点继续拆分为编队识别、编队调整和编队选船：识别产生当前事实，
  调整消费 YAML 规则并产生目标/变更计划，选船负责船池搜索、候选校验和单舰替换执行。
- 辅助功能承载补给、战役支援、维修等可独立触发的业务流程；每项按业务功能建包，不能用
  `utils`、`helpers` 或笼统状态检查包收纳未分类代码。
- 损伤识别属于维修流程所需事实时由维修模块拥有；舰名、舰种、等级、槽位占用等用于编队
  规划的事实由编队识别拥有，禁止两边复制同一识别实现或共享可写状态。
- 当前 `main_page/page.py` 同时转发页面操作、舰队识别、换船、补给和维修，并通过
  `__getattr__` 暴露 `FleetChangeController`；它是兼容聚合器，不是目标页面控制器。
- 当前 `fleet_change` 由 `_detect -> _rules -> _planning -> _selection -> _alignment ->
  _change -> campaign` 的 Mixin 继承链组成，`FleetChangeController` 又通过
  `__getattribute__`/`__getattr__` 回调页面；目标结构必须改为流程节点的显式调用。
- 当前 `shipyard_page/page.py` 同时包含搜索框操作、候选卡 OCR、约束判断和点击执行；目标上
  它属于“编队选船”节点，不再作为与选船核心平级的 Fleet 一级页面包。
- 页面控制器不是纯原子动作集合：按用户已确认的 Battle Page 样板，`main_page/page.py`
  顶部应提供“确认准备页 -> 选择舰队 -> 调用选船核心 -> 调用辅助流程 -> 点击进入战斗”的
  主流程，随后才排列页面检查和原子 UI 方法；不再另设根 `workflow.py` 聚合层。
- 页面身份、当前舰队标签和当前面板等非 OCR 页面状态归 `main_page`；舰名/舰种/等级/槽位
  OCR 归选船核心的编队识别；血条损伤识别归辅助功能的维修包；自动补给和战役支援状态
  分别归各自辅助包，避免建立横向 `fleet_status` 杂项模块。
- `start_battle`、`try_start_battle` 和 `go_back` 是准备页面本身的 UI/终态动作，归
  `main_page`，不再创建旧任务书提出的 `departure` 一级流程。
- 当前原始 YAML 的加载、字段验证和预设转换位于 `business.combat` 配置入口，Fleet 实际
  接收 `FleetSlotRule`/`ShipSelector`；“YAML 识别”在选船核心中应定义为理解和执行这两个
  规范化模型所表达的主选、备选、舰种和等级规则，不把文件 I/O 或 Schema 下沉到 UI。
- `FleetSlotRule`、`ShipSelector` 是无 UI 依赖的共享值对象，继续由 `common.fleet` 拥有；
  选船核心消费它们，不复制第二套模型或维护第二套 YAML 解析结果。

## 2026-09-12 Fleet F0 Definition Inventory

当前 Fleet 源目录包含 30 个 Python 文件。以下为本轮 AST 盘点出的全部 class、method 和
顶层函数；它们必须在迁移表中各自拥有唯一目标，不得按文件整体搬迁后再猜职责。

- `main_page/page.py`：`BattlePreparationPage.__init__`、`prepare_and_start_battle`、
  `check_current_page`、`check_auto_supply_enabled`、`read_selected_fleet`、
  `read_active_panel`、`_preferred_ocr`、`select_fleet`、`select_panel`、
  `click_ship_slot`、`toggle_auto_supply`、`open_quick_supply`、`open_quick_repair`、
  `start_battle`、`try_start_battle`、`go_back`、`detect_ship_damage`、
  `detect_fleet_info`、`_recognize_fleet_levels`、`_recognize_fleet_ship_types`、
  `_best_ship_type_from_results`、`_parse_level`、`detect_fleet`、`detect_fleet_snapshot`、
  `fill_missing_fleet_snapshot`、`change_fleet`、`validate_campaign_fleet`,
  `last_changed_fleet`、`check_support_enabled`、`toggle_battle_support`、`supply`、
  `apply_supply`、`check_repair`、`repair_slots`、`apply_repair`、`__getattr__`、
  `FleetInfo` 类属性挂载。
- `main_page/preparation/operations.py`：`select_fleet`、`select_panel`、
  `click_ship_slot`、`switch_auto_supply`、`open_quick_supply`、`open_quick_repair`、
  `start_battle`、`try_start_battle`、`go_back`。
- `main_page/preparation/recognition.py`：`check_current_page`、
  `check_auto_supply_enabled`、`read_selected_fleet`、`read_active_panel`。
- `main_page/preparation/constants.py`：`Panel` 枚举。
- `main_page/fleet_status/operations.py`：`FleetInfo.to_ships`、`read_fleet_info`。
- `main_page/fleet_status/recognition.py`：`detect_ship_damage`、`read_fleet_levels`、
  `read_fleet_ship_types`、`_best_ship_type_from_results`、`_parse_level`、
  `_best_level_from_results`。
- `main_page/fleet_change/_detect.py`：`FleetSnapshot.unknown_slots`、
  `FleetSnapshot.unknown_type_slots`、`FleetSnapshot.unknown_level_slots`、
  `FleetSnapshot.has_unknown_details`、`FleetDetectMixin._match_context_ship_name`、
  `detect_fleet`、`_recognize_fleet_names_at_slots`、`detect_fleet_snapshot`、
  `fill_missing_fleet_snapshot`。
- `main_page/fleet_change/_rules.py`：`FleetRuleMixin._option_matches_name`、
  `_slot_options`、`_matches_search_name`、`_option_for_name`、
  `_requires_selection_validation`、`_snapshot_satisfies_option`、`_slot_matches`、
  `_validate_with_selector`。
- `main_page/fleet_change/_planning.py`：`FleetPlanningMixin._plan_target_options`、
  `_ocr_target_pool`、`_target_names`、`_validate_assignment`、`_member_set_satisfied`、
  `_mark_snapshot_verified_slots`、`_match_existing_members`、`_assignment_locations`、
  `_target_order`、`_replacement_slot`。
- `main_page/fleet_change/_selection.py`：`_ShipSelection` 数据类、
  `FleetSelectionMixin._open_choose_page`、`_cancel_choose_page`、
  `_try_select_option`、`_change_single_ship`。
- `main_page/fleet_change/_alignment.py`：`_UnresolvedPrimaryError`、
  `FleetAlignmentMixin._deferred_primary_slots`、`_select_deferred_fallback`、
  `_try_deferred_primary`、`_resolve_deferred_primaries`、`_align_member_set`、
  `_remove_extra_members`、`_full_align`、`_local_fix`、`_reorder`、`_circular_move`。
- `main_page/fleet_change/_change.py`：`FleetChangeMixin._emit_fleet_event`、
  `last_changed_fleet`、`_merge_position_snapshot`、`_snapshot_option_match_result`、
  `_snapshot_slot_match_result`、`_log_snapshot_debug`、`_assignment_failure_reason`、
  `_log_final_result`、`_detect_position_snapshot`、`_prepare_members_for_reorder`、
  `change_fleet`、`_level4_detail_requirements`、`_retry_invalid_strict_details`、
  `_detect_initial_snapshot`。
- `main_page/fleet_change/campaign.py`：`CampaignFleetChangeMixin.change_fleet`、
  `validate_campaign_fleet`、`_change_campaign_fleet`、`_clear_campaign_fleet`、
  `_replace_campaign_slots`、`_select_campaign_slot`、`_clear_campaign_slot`、
  `_campaign_slot_satisfied`、`_finish_campaign_fleet`。
- `main_page/fleet_change/decisive_fleet.py`：`change_decisive_fleet`。
- `main_page/fleet_change/operations.py`：`FleetChangeController.__init__`、
  `__getattribute__`、`__getattr__`、`create_controller`、`change_fleet`。
- `shipyard_page/page.py`：`_CardConstraintResult.is_fallback`、
  `fallback_priority`、`ChooseShipPage.__init__`、`check_current_page`、
  `open_search_box`、`input_ship_name`、`dismiss_keyboard`、`click_remove_ship`、
  `select_single_ship`、`_normalize_hit_entry`、`_is_level_in_range`、
  `_check_hit_constraints`、`_click_ship_in_list`、`_detect_ship_type_in_single_card`、
  `_extract_ship_type_from_text`、`_is_ship_type_in_rule`、`_normalize_search_keyword`、
  `_matches_ship_name`、`_preferred_ocr`、`_detect_hit_ship_type`、
  `_wait_leave_current_page`。
- `main_page/repair/operations.py`：`RepairStrategy`、`check_repair`、`repair_slots`、
  `apply_quick_repair`。
- `main_page/supply/operations.py`：`switch_battle_support`、`supply`、`apply_supply`。
- `main_page/supply/recognition.py`：`check_support_enabled`。
- `__init__.py` 中的包级 `__getattr__` 以及所有 `__all__` 重导出也属于 F0 审计对象，
  但不作为业务方法迁移。

F0 外部引用初步结果：生产业务主要从 `fleet.main_page` 取得 `BattlePreparationPage`，
示例和 E2E 工具也使用该页面；现有 UI/业务测试还直接 patch 或导入旧的深层实现，包括
`fleet_change._detect`、`fleet_change._change`、`main_page.preparation`、
`main_page.fleet_status` 和 `shipyard_page`。这些深层测试引用不能直接视为新 API，必须在
后续按业务行为迁移或按旧兼容测试删除。

当前发现的运行期可写状态包括页面保存的 `_ctx`、`_ctrl`、`_ocr`、`_ship_ocr`、
`_fleet_change`，以及旧换船控制器保存的 `_last_changed_fleet`、`_initial_snapshot`、
`_on_fleet_event`。前四项是注入引用，后三项分别是待删除的旁路结果、识别中间状态和
事件 callback 状态，F0 必须继续追踪其所有读写方。

F0 生产消费者清单：

- `business.combat.bettle.normal_fight`：创建准备页、选择舰队、换船、补给、维修并启动普通战斗。
- `business.combat.exercise.operations`：创建准备页、读取/应用演习编队和维修策略。
- `business.combat.campaign.operations`：创建准备页、执行战役舰队校验/换船和维修策略。
- `business.combat.decisive.handlers` 与 `operations.sortie_page.decisive_page.map_page`：
  创建准备页、决战换船/维修和准备页检查。
- `application.combat.support` 与 `business.logistics.repair.quick_repair`：调用准备页或维修
  子模块完成支持流程。
- `application.ui.navigation.registry`、`navigation.service`、主页活动导航和 sortie 页面：
  注册或等待准备页检查，并执行准备页返回。
- `examples/change_fleet.py`、`tools/ocr_change_fleet_e2e`：直接作为手工/端到端入口创建页面。

F0 非生产引用主要集中在 `testing/ui/battle_preparation`、战役/普通/导航测试和旧页面
E2E；其中同时存在真实行为断言与旧私有路径 patch，不能一次性全部保留或全部删除。

生产流程补充结论：普通、演习、战役和决战业务当前各自编排舰队选择、补给、维修、战前
状态读取和出征；Fleet 重构后这些页面动作应收敛到 `main_page` 的主流程入口，但任务
上报、战斗次数耗尽、澡堂导航和任务状态仍属于业务/导航层，不得下沉到 Fleet。

F0 直接消费者按迁移性质分组：

- 生产入口：`business/combat/bettle/normal_fight.py`、`business/combat/exercise/operations.py`、
  `business/combat/campaign/operations.py`、`business/combat/decisive/handlers.py`，需要改为
  调用新的页面主流程并继续保留各自业务状态机职责。
- 决战页面和导航：`operations/sortie_page/decisive_page/map_page.py`、
  `decisive_page/preparation_page.py`、`decisive_page/legacy_fleet_change.py`、
  `application/ui/navigation/registry.py`、`navigation/service.py`；其中决战旧准备页继承
  和旧算法入口应在 F0 标为删除/重写，不得继续保留兼容。
- 其他生产调用：`application/combat/support.py`、`business/logistics/repair/quick_repair.py`、
  `home/event_page/page.py`、普通/战役/演习 sortie 页面、`common/system/config_compat.py`。
- 行为测试：`testing/ui/battle_preparation/test_unit.py`、
  `testing/ui/battle_preparation/test_decisive_fleet_branch.py`、
  `testing/ui/battle_preparation/test_main_page_flow.py`、
  `testing/ui/test_choose_ship_page.py`、战役/演习业务测试、普通战斗与澡堂导航测试；
  测试中既有新行为验证也有旧私有 patch，须逐项迁移或删除。
- 工具、示例和文档：`examples/change_fleet.py`、`tools/ocr_change_fleet_e2e/`、
  `docs/architecture/`、`docs/developer/`、`docs/features/`、`docs/usage/`；其中代码工具
  随 API 迁移，文档只同步最终入口，不保留失效路径说明。

F0 当前定义的初步唯一归属：

- `main_page` 保留准备页 `check_current_page`、`read_selected_fleet`、`read_active_panel`、
  `select_fleet`、`select_panel`、`click_ship_slot`、`start_battle`、`try_start_battle`、
  `go_back` 和 `prepare_and_start_battle`；页面方法直接调用 `main_page.constants`，不再
  通过 `preparation` 包转发。
- `formation/fleet_recognition` 接收 `FleetSnapshot`、舰名/槽位/舰种/等级识别和纯解析；
  `main_page` 上的 `detect_fleet`、`detect_fleet_snapshot`、`fill_missing_fleet_snapshot`
  只作为主流程调用该节点的过渡定义，最终不保留页面转发方法。
- `formation/fleet_adjustment` 接收规则匹配、主选/备选规划、成员集合调整、移除、排序、
  复查以及战役/决战分支；`change_fleet` 和 `validate_campaign_fleet` 改为该节点入口。
- `formation/ship_selection` 接收 `_selection.py` 和 `shipyard_page/page.py` 的船池 UI、
  候选 OCR、约束筛选、单舰选择/移除和选船页退出；`ChooseShipPage` 旧类名不保留。
- `support/supply` 接收自动补给状态、自动补给切换、快速补给打开和补给动作；
  `support/campaign_support` 接收战役支援识别和切换；`support/repair` 接收损伤识别、
  修理策略、快速维修、复查和手动维修中断。
- `detect_fleet_info`、`FleetInfo`、`FleetInfo.to_ships`、`last_changed_fleet`、
  `_preferred_ocr`、页面私有算法挂载和三个动态代理目前标为“拆分后删除”，最终以 F0
  消费者核对决定替代结果契约，不恢复旧聚合器。

F0 结果模型结论：`FleetInfo` 只是把舰队编号、等级和损伤再次聚合，并由 `to_ships` 创建
`SimpleNamespace` 供业务临时消费；它没有独立页面事实所有权。目标应由编队识别返回
`FleetSnapshot`，维修返回明确的损伤/修理结果，业务层需要的战斗对象由业务层自行转换，
不在 Fleet 保留第二个聚合模型。

F0 决战分支结论：`decisive_fleet.py` 通过设置 `_use_search`、写入
`_last_changed_fleet`、调用页面私有 `_change_single_ship`/`_reorder`/`_validate_with_selector`
完成决战编队；这是旧 Mixin 边界泄漏，目标迁入 `formation/fleet_adjustment/decisive.py`
后改为显式调用编队识别、调整和选船入口。

F0 输入边界确认：`business/combat/fleet.py` 已集中拥有 YAML/API 槽位转换、舰种代码解析、
主选/备选规则模型和舰队选择优先级；Fleet 不应复制这些入口。需要迁移的是它们的 UI
消费者，不是把 YAML 解析器再搬进 Controller。

F0 兼容点确认：`fleet/__init__.py` 当前没有公共出口，`main_page/__init__.py` 通过包级
`__getattr__` 延迟提供页面类，`business/logistics/repair/quick_repair.py` 通过
`sys.modules` 把旧模块替换成维修包；这些都是任务书明确要求删除的兼容机制。

F0 特殊页面确认：`application/ui/navigation/registry.py` 是选船页面检查器的唯一生产注册
方；决战 `preparation_page.py` 和 `legacy_fleet_change.py` 仍各自依赖旧准备页/换船入口，
后续必须改为 `formation` 选船核心与 `main_page` 的明确入口，不能保留第二套决战页面流程。

F0 校准归属确认：现 `preparation/constants.py` 混合准备页基础控件、自动补给和面板校准；
`fleet_status/constants.py` 混合血条、等级和舰种 ROI；`repair/constants.py` 又引用血条
坐标；`supply/constants.py` 混合战役支援和补给时序。重构时按业务拥有者拆开，不能把这些
映射原样复制到多个新包。现有舰种 ROI 还包含高于四位的小数，属于 OCR/ROI 专项中需要
保留校准精度、不能机械四舍五入的内容。

F0 测试边界确认：`testing/ui/battle_preparation/test_unit.py` 既覆盖页面原子动作，也覆盖
大量编队识别、规则规划、决战分支和旧私有 patch；`test_choose_ship_page.py` 直接覆盖船池
卡片筛选。后续应按三个选船节点和三个辅助流程重新分组，旧路径 patch 全部删除，不把
这份混合测试继续作为新模块的入口契约。

F0 页面基础实现确认：当前准备页的页面模板检查、舰队标签读取、面板读取、舰队/槽位/面板
点击、开始出征和返回动作都可以直接下沉到 `main_page/page.py`；`check_current_page` 不是
OCR 规则，而是 `Templates.Page.BATTLE_PREP` 模板匹配。`try_start_battle` 只需要改为调用
页面自身的 checker，不需要保留独立 `preparation.recognition` 模块。

## 2026-09-12 Fleet F1 Page Controller Started

- 已将 `main_page/page.py` 改为只包含准备页主流程、页面检查、舰队/面板读取、槽位/面板
  点击、开始出征和准备页返回；删除旧页面上的识别、换船、补给、维修和动态代理出口。
- 已将准备页校准物理迁移到 `main_page/constants.py`，删除独立 `preparation` 包文件；
  自动补给和战役支援等配置待对应辅助包迁移时进一步分离。
- F1 期间旧 `preparation` 路径仍被尚未迁移的旧辅助/换船实现引用，属于明确的中间断点；
  不创建兼容 re-export，后续阶段直接改调用方。

## 2026-09-12 Fleet F2 Formation Recognition Started

- 已建立 `formation/fleet_recognition/`，将 `FleetSnapshot` 与舰名、槽位占用、舰种、等级
  识别统一放入识别节点；识别函数只接收截图和显式 OCR 引擎。
- 旧 `main_page/fleet_change/_detect.py` 和 `main_page/fleet_status/` 已删除，页面不再
  暴露舰队识别转发方法；旧换船代码的引用将在 F4/F5 重写时直接迁移。
- 编队识别节点保留现有 OCR 匹配行为，未创建新的 OCR 引擎或上下文；`_fuzzy_match` 私有
  依赖仍按既有 OCR 专题范围处理。

F2 视觉边界待 F8 决定：编队识别需要知道槽位是否有船，当前临时通过血条探测点和
`classify_blood` 得到布尔占用状态；维修又需要同一探测点得到损伤状态。后续不得在两个
模块复制颜色分类逻辑，应由 `main_page` 主流程协调一次识别结果，或将无业务语义的像素
分类下沉到 common 后由两个业务包消费。当前不在 F2 扩大范围。

F2 验证样例修正：项目 `SHIP_LEVEL_MAX` 为 110，首次 smoke 使用 `Lv. 120` 不符合当前
等级范围；该失败不代表识别迁移失败，后续使用项目允许的等级输入验证。

## 2026-09-12 Fleet F3 Ship Selection Started

- 已建立 `formation/ship_selection/`，将船池页面拆为 `page.py` 页面动作、`recognition.py`
  船卡 OCR/约束判断和 `workflow.py` 搜索/滚动/点击/移除流程。
- `ShipSelectionPage` 只持有调用方注入的上下文和设备引用；选船工作流通过页面公开原子
  方法操作设备，不再依赖准备页私有属性或 Mixin。
- 已删除旧 `shipyard_page/` 和 `fleet_change/_selection.py`；现有 `_fuzzy_match` 仅按原
  语义迁移到识别模块，未在本阶段优化 OCR。

## 2026-09-12 Fleet F4 Adjustment Migration Started

- 已将旧 `_rules.py`、`_planning.py`、`_alignment.py`、`_change.py`、`campaign.py` 和
  `decisive_fleet.py` 物理迁移到 `formation/fleet_adjustment/`，下一步把 Mixin 改为
  `FleetRules`、`FleetPlanner`、`FleetAlignment` 和 `FleetAdjustment` 的显式组合。
- 规则和规划模块可以保持无状态；对齐和调整流程需要保存当前快照、有限重试和页面/上下文
  引用，这些状态必须只属于 `FleetAdjustment`，不能继续散落在类属性或页面对象上。
- 决战分支当前直接操作页面私有 `_change_single_ship`、`_reorder` 和 `_validate_with_selector`；
  F4 必须改为调整流程对象调用选船节点和页面公开动作。

F4 算法内部结构确认：旧 `_change.py` 是实际的普通/活动/演习调整主流程，包含快照合并、
验证日志、初始四轮识别、成员集合调整、排序和局部重试；旧 `_alignment.py` 是成员替换、
删除和拖拽实现；`_planning.py` 的规划函数与 `_rules.py` 的规则函数可无状态化。目标应
保留这些业务阶段，但把状态集中到 `FleetAdjustment`，不把每个算法阶段继续拆成新的一级
模块或用代理串联。

F4 旧战役分支确认：原 `campaign.py` 通过继承通用换船类复用规划、识别和单槽选择，只把
“清空不压缩、固定物理槽位、点对点换船”作为差异；重构后这些差异保留为
`fleet_adjustment/campaign.py` 的函数，接收 `FleetAdjustment` 的显式操作依赖，不新增
页面类或继承层。

F4 旧决战分支确认：原 `decisive_fleet.py` 同时承担目标匹配、单舰替换、清空多余舰船和
拖拽排序；重构后保留为 `fleet_adjustment/decisive.py` 的模式流程，具体识别、选船和页面
动作分别调用已有节点，不在决战文件复制通用逻辑。

F4 当前实现确认：`FleetAdjustment` 以显式 `FleetAlignment`、`FleetPlanner` 和页面对象
组合；`rules.py` 与 `planning.py` 不再依赖识别 Mixin。通用、战役、决战调整均统一返回
`FleetSnapshot` 或抛出明确异常，旧的 `bool` 成功值和 `last_changed_fleet` 已从新流程中移除。

## 2026-09-12 Fleet F6 Supply Migration Complete

- 已建立 `support/supply/`，迁移自动补给状态识别、自动补给切换、快速补给面板和指定槽位
  补给流程；补给坐标与时序集中在本包 constants。
- 已删除旧 `main_page/supply/`，页面主流程改为显式调用 `apply_supply(ctx, page)`；战役支援
  代码没有混入补给包，待 F7 单独迁移。
- 验证：目标 pre-commit、compileall、自动补给开关分支 smoke 和 `git diff --check` 通过；
  未运行旧路径测试，未执行实机验证。

## 2026-09-12 Fleet F7 Campaign Support Complete

- 已建立 `support/campaign_support/`，将战役支援颜色识别、启用/关闭切换和切换后复查
  从 supply 中独立出来。
- 支援状态使用 `ENABLED`、`DISABLED`、`EXHAUSTED` 三态；耗尽时不再把状态压成可点击的
  布尔值，关闭请求直接失败，不误触发消耗性操作。
- 验证：目标 pre-commit、compileall、三态识别 smoke、切换复查 smoke 和
  `git diff --check` 通过；未运行旧路径测试，未执行实机验证。

## 2026-09-12 Fleet F8 Repair Complete

- 已建立 `support/repair/`，迁移损伤识别、`RepairStrategy`、快速维修、复查和有限重试；
  血条探测点由 `main_page.constants` 唯一拥有。
- 手动维修不再接收跨页面 callback，直接抛出带槽位的 `ManualRepairRequiredError`；澡堂
  导航继续由业务/导航层负责。
- 已删除旧 `main_page/repair/`，页面主流程改为显式调用 `apply_repair(ctx, page, strategy)`。
- 验证：目标 pre-commit、compileall、无损伤/快速维修/手动中断/策略判断 smoke 和
  `git diff --check` 通过；未运行旧路径测试，未执行实机验证。

## 2026-09-12 Fleet F9 Consumer Migration Started

- 生产层的普通、演习、战役和决战流程目前仍分别调用准备页的换船、补给、维修、损伤
  读取和出征方法；新的根入口需要逐步替换这些能力组合，不能只改 import 名称。
- 根包将公开 `BattlePreparationPage`、`FleetSnapshot` 和 `RepairStrategy` 等稳定契约；
  选船节点和辅助包内部实现不作为业务深层入口。
- 导航注册需要船池页面只读 checker；该 checker 作为根包的注册专用入口，业务代码不得
  以此穿透 `formation/ship_selection`。

F9 当前迁移顺序：先更新 `navigation.registry` 的准备页/船池 checker 和
`navigation.service` 的准备页返回入口，再更新普通、演习、战役、决战业务对准备流程的
调用；决战 `preparation_page.py`/`legacy_fleet_change.py` 属于旧兼容实现，直接删除或
改为新 `formation` 入口，不保留第二个决战准备类。旧测试中只 patch 私有路径的部分按
任务书删除，仍验证主流程行为的部分迁移到新入口。

F9 第一批迁移结果：生产代码中准备页构造已统一为只传入运行上下文，准备页/船池页面
checker 已改为从 Fleet 根包取得；剩余旧路径集中在决战兼容页面、维修兼容别名和测试/文档，
不再有新的生产模块从 `fleet.main_page` 或 `fleet.shipyard_page` 导入。

F9 决战兼容清理结果：`decisive_page/preparation_page.py` 和
`decisive_page/legacy_fleet_change.py` 已删除，决战页面包不再导出旧准备页子类或旧算法
开关。决战地图和状态机后续必须通过 `BattlePreparationPage` 的新页面流程出口接入。

F9 业务调用语义确认：普通战斗当前依赖“调整后的舰名 + 损伤/等级组成的战斗 Ship 对象”，
战役还依赖编队事件断点和战役次数耗尽回退，演习依赖先编队后单独出征，决战依赖节点状态
机和澡堂维修分支。新的 `FleetSnapshot` 不再提供旧 `FleetInfo.to_ships`，这些业务结果
转换必须留在各自业务层，Fleet 只返回页面事实和明确维修异常。

F9 页面入口迁移结果：`BattlePreparationPage` 现在提供 `adjust_fleet`、
`read_fleet_snapshot`、`read_ship_damage`、`apply_supply`、`apply_repair`、
`check_repair`、`validate_campaign_fleet` 和准备页返回出口；这些是显式页面流程调用，不是
动态代理。普通、战役、演习、决战生产调用已切到这些入口，导航注册通过根包 checker 完成。

F9 测试迁移结果：页面主流程、决战入口、澡堂导航和船池节点已有新契约测试；原
`testing/ui/battle_preparation/test_unit.py` 已删除，因为它整体依赖旧 Mixin/私有 patch。
战役与普通业务测试仍包含旧页面方法的替身和断言，需要继续按新 `adjust_fleet`、快照和
损伤读取结果迁移，不能为它们恢复旧 API。

F10 续作预检：当前绑定仍指向 `codex/20260830-autowsgr-upgrade`，任务书已重读并确认
F0-F9 完成、F10 未完成。现有风险集中在旧路径/旧符号扫描，以及普通/战役业务把
`FleetSnapshot` 转换为运行时 `Ship` 的行为复核；本阶段不修改 `bath_page`，不恢复旧兼容。

F10 首轮静态扫描：Fleet 当前文件树只有 `main_page`、`formation`、`support` 三个一级
边界，Fleet 内没有 `Mixin`、`FleetChangeController`、`create_controller`、
`last_changed_fleet`、动态属性代理或旧 Fleet 路径。仍发现根包/节点内部及测试中的若干
深层导入，需按“稳定根入口、节点内实现边界、测试是否只验证真实业务”的规则逐项复核；
普通和战役业务均把快照舰名通过 `ctx.get_ship()` 转成运行时舰船，需确认这是业务层的
唯一转换且不应回收到 Fleet。

F10 文件初查：`main_page/page.py` 已包含准备页主流程和页面原子动作，`formation` 已
按识别/调整/选船分包，`support` 已按补给/战役支援/维修分包；未发现旧 Mixin 或动态
代理实现。待核对项是根包是否应经 `formation.fleet_recognition` 公开出口导出模型、
节点内部是否存在可消除的跨边界深层导入，以及 `page.py` 中局部导入是否只是为避开
循环依赖而遗留的实现细节。

F10 导入图复核：`ship_selection.page` 顶层导入 `main_page.page` 仅为 `go_back` 提供
准备页 checker；由于 `main_page.page` 的流程入口会调用 `formation`，该依赖形成
`main_page -> formation -> ship_selection -> main_page` 的反向循环。调用方已有真实的
`BattlePreparationPage.check_current_page`，应将 checker 作为显式参数传入选船页面返回
动作，消除反向导入而不增加兼容层。Fleet 根包的 `FleetSnapshot` 也应从
`formation.fleet_recognition` 的公开出口导入，避免直接穿透 `models.py`。

F10 修正后复核：根包已通过 `formation.fleet_recognition` 公开出口导出 `FleetSnapshot`，
选船页面返回动作已接收调用方 checker，Fleet 的实际运行时导入不再有页面反向依赖。
普通/战役业务使用 `ctx.get_ship()` 将快照名称映射到运行时 `Ship`，这是业务层唯一转换，
Fleet 保持只返回识别事实；迁移后的 `common/fleet.py` 仍需补齐项目统一文件级说明。

F10 旧词扫描：当前 Fleet 源码旧目录、Mixin、动态代理、旧 Controller 名称和旁路状态均
已清零；仓内剩余 `fleet_change` 主要是历史文档和 `use_new_fleet_change_algorithm`
配置/API。后者只在 `common.system.config`、`server.schemas`、`server.routes.task` 和
旧配置测试中出现，未发现运行时代码消费者，符合无消费者旧兼容 API 的删除候选；文档
历史引用需在最终报告中区分为历史记录还是当前契约。

F10 旧兼容清理：已删除 `use_new_fleet_change_algorithm` 的配置字段、决战请求字段、
路由透传和只验证该开关的两个旧测试；当前 `autowsgr`、`testing`、`tools`、`examples`
和 `docs` 均不再出现该符号。历史报告中仍可能出现旧架构文件名，但不再是可导入或可
执行的当前契约。

F10 状态收敛：`FleetAdjustment` 不再保存自己的 `_initial_snapshot`，初始快照只由
`FleetAlignment` 持有并用于重规划后的已验证槽位标记；未复制新的状态源，也未改变
调整流程的快照输入输出。

F10 行为门禁：Fleet 主流程、准备页、识别/调整/选船、补给/维修、澡堂导航以及普通、
战役、演习调用方 focused 测试共 `90 passed`；当前快照到运行时 `Ship` 的业务层转换和
手动维修异常路径均通过现有替身契约验证。

F10 配置/API 回归：删除无消费者决战换船开关后，`testing/infra/test_config.py` 与
`testing/test_server_schemas.py` 共 `140 passed`；首次运行的 12 个错误仅是 Windows
pytest 临时目录父路径不存在，创建工作区内忽略目录后重跑通过。

F10 快照状态复核：初始 `FleetSnapshot` 由 `FleetAdjustment` 唯一持有，对齐节点通过
`_full_align`/`_local_fix` 显式接收同一快照；战役和决战模式仍从该编排器读取快照字段，
focused 回归再次 `90 passed`。没有恢复 `FleetAlignment` 的影子快照属性。

F10 配置布局复核：Fleet 全部校准配置仍位于各自 `constants.py`，识别文件只保留 OCR
算法参数，页面文件没有定义坐标、ROI 或颜色；字典型配置已补充整体业务语义注释。
迁移到 `common/fleet.py` 的规则值对象已补齐通用文件说明。Scoped pre-commit 第二轮
所有钩子通过。

F10 import 规范收紧：严格静态门禁初次发现 Fleet 内仍有 `numpy as np` 和
`UIContext as GameContext` 语义别名；已统一改为真实导入名和真实类型名，当前 Fleet
代码不再含 import `as` 别名，也没有私有 `from` 导入。

F10 最终验证结论：编译、Fleet 根入口导入、导航注册入口、准确运行时依赖图和静态结构
门禁均通过；最终 focused 回归共 `230 passed`。受影响源码未执行真实游戏/模拟器 E2E，
因此页面像素校准、OCR 稳定性和跨模式实机返回路径仍不能由本次测试证明。

F10 已关闭：最终 scoped pre-commit（包含综合报告、任务书和计划文件）全部通过，
`git diff --check` 通过；任务书 F10、`task_plan.md` Phase 32 和综合报告均已完成。
当前工作区仍包含本任务之前的大量未提交架构迁移，未执行任何提交或清理；本任务新增的
pytest 临时目录因安全守卫拒绝递归删除而保留，内容仅为测试临时文件。
