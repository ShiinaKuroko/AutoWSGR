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
