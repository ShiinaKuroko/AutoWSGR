# UI Controller 样板与三模块重构综合报告

日期：2026-09-07
任务：`20260830-sakuya-exercise-consolidated-7a6c`
分支：`codex/20260830-sakuya-exercise-consolidated-7a6c`
状态：待人工 review

## 1. 目标与边界

本批完成以下工作：

1. 修复浴室浮层关闭成功判断不一致的问题。
2. 以现有 `bath_page` 的有效职责为参考，编写 UI Controller 页面规范。
3. 按规范重写 `build_page`、`backyard_page`、`canteen_page`。
4. 使用 Ponytail 检查本批是否引入无必要抽象，并归档上下文/OCR 问题。

明确边界：

- `bath_page` 只为第 1 项做了最小必要修改；没有为了套用新目录样板而重构它。
- 上下文/OCR 专题没有在本批实现，相关问题写入 `[todo]` 台账。
- 没有新增依赖、兼容层、第二套状态源或空的 OCR 文件。
- 当前 AutoWSGR worktree 中原先已有的 Bath/Exercise 未提交改动被保留；本报告只
  把本批新增的结构、命名和状态判断列为本批工作。

## 2. A1：浴室浮层关闭状态修复

文件：`AutoWSGR/autowsgr/application/ui/controller/bath_page/page.py`

修复内容：

- “全部修理”自动关闭路径现在同时确认当前画面仍是浴室页面且选择修理浮层已经消失。
- “全部修理”手动点击关闭后复用已有 `_wait_overlay_close()`，确认点击确实生效；
  失败时抛出 `NavigationError`，不再点击后睡眠再直接返回。
- 保留三种业务语义：主动导航关闭、选船后判断修理结果、全部修理后的收尾。

本批没有修改浴室坐标、OCR、上下文或其他页面行为。

## 3. A2/A3：页面规范

文件：`[规范]ui-controller-code-style.md`

规范要点：

- 页面使用 `xx_page/` 包目录；稳定入口由 `__init__.py` 导出。
- 页面专用坐标、颜色和视觉参数放在私有 `constants.py`，点击坐标使用四位
  `0.xxxx` 相对格式，每项带业务语义注释。
- `page.py` 只负责页面检查、可见状态、点击、打开/关闭、等待和页面回退。
- `recognition.py` 只负责页面拥有的 OCR 规则；没有 OCR 的页面不创建空文件。
- 状态检查统一使用 `check_*`，可见状态读取使用 `read_*`，动作使用对应的
  `open_*`、`close_*`、`select_*`、`click_*`、`confirm_*`、`cancel_*`、
  `dismiss_*` 前缀。
- 函数按业务调用链排序，不按字母排序；上下文、页面、通用视觉和 OCR 的所有权
  不互相越界。

## 4. A4：三个页面模块

### `build_page`

- 从单文件迁移为 `build_page/__init__.py`、`constants.py`、`page.py`。
- 建造、槽位、解体筛选、确认和动画坐标已私有化为四位相对坐标。
- `BuildPage.is_current_page` 改为 `check_current_page`，
  `get_active_tab` 改为 `read_active_tab`。
- 解体动作统一为 `click_*`、`open_*` 和 `confirm_*` 前缀。
- `ShipType.relative_position_in_destroy` 页面坐标属性已移除，坐标归还建造页常量。
- 删除无其他消费者的 `common/calibration/build.py` 和对应坐标 YAML。
- 页面没有 OCR，因此没有创建 `recognition.py`。

### `backyard_page`

- 从单文件迁移为 `backyard_page/__init__.py`、`constants.py`、`page.py`。
- 后院返回、浴室入口和食堂入口坐标已私有化。
- `BackyardPage.is_current_page` 改为 `check_current_page`，并同步所有仓库内调用方。
- 页面没有 OCR，因此没有创建 `recognition.py`。
- 删除无其他消费者的 `common/calibration/backyard.py` 和对应坐标 YAML。

### `canteen_page`

- 从单文件迁移为 `canteen_page/__init__.py`、`constants.py`、`page.py`。
- 返回、菜谱、覆盖确认、取消、弹窗和动画坐标已私有化。
- `CanteenPage.is_current_page` 改为 `check_current_page`，
  `click_to_skip_animation` 改为 `click_skip_animation`。
- 页面没有 OCR，因此没有创建 `recognition.py`。
- 删除无其他消费者的 `common/calibration/canteen.py` 和对应坐标 YAML。

### 调用方同步

已同步页面注册、导航图、业务物流入口、测试框架和三个相关 E2E 脚本。旧的目标页面
检查名、旧校准导入、旧解体动作名和相对导入扫描均无残留。

## 5. Ponytail 审查

审查结论：本批没有发现应删除的新增抽象。

- 没有新增 Manager、Factory、Registry、兼容别名或新依赖。
- 三个页面的包目录、私有常量和包级导出均有真实调用方，是本任务明确要求。
- 没有创建空 `recognition.py`，避免为目录形式增加无意义文件。
- 页面坐标从公共校准包装和 `ShipType` 页面属性迁回页面模块，减少了公共层泄漏。
- 目标页面未新增上下文或 OCR 逻辑；已有问题保留到专项台账。

## 6. TODO 台账

- `[todo]上下文问题汇总.md`：`BathPage` 重新创建 OCR、绕过 `ctx.ocr` 的上下文所有权问题。
- `[todo]其他模块与OCR模块之间的兼容冲突.md`：多个模块直接依赖 OCR 私有
  `_fuzzy_match()` 的兼容边界问题。

上述问题按用户要求暂不在本批修复。

## 7. 验证结果

| 检查 | 结果 |
|---|---|
| 目标包及调用方 `python -m compileall -q` | 通过 |
| 页面包结构、坐标格式和旧文件断言 | 通过 |
| 旧导入、旧方法名和旧页面坐标引用扫描 | 通过 |
| 新页面包行宽检查（<= 100） | 通过 |
| `git diff --check` | 通过 |
| Python runtime import smoke | 未通过：环境缺少 `cv2` |
| YAML 坐标加载 smoke | 未通过：环境缺少 `yaml` |
| Ruff | 未执行：`ruff` 不在环境中，`uv run --no-sync` 也找不到可执行文件 |
| pre-commit | 未执行：命令不可用 |
| pytest | 未执行：命令不可用，且不是本批单独目标 |
| 模拟器/实机 E2E | 未执行：当前环境没有设备验证条件 |

未执行的检查没有被宣称为通过。现有 AutoWSGR 代码改动仍处于未提交状态，未暂存、未
提交、未推送。

## 8. Review 重点与剩余风险

- 重点确认重命名后的 `check_current_page`、`read_active_tab` 是否需要兼容仓库外部
  消费者；仓库内调用方已全部同步。
- 重点确认 `build_page` 删除的公共校准包装和 `ShipType` 页面属性没有仓库外隐藏消费者。
- 运行环境补齐 `cv2`、`yaml`、Ruff 和 pre-commit 后，应重新执行 runtime import、
  focused 测试和 lint。
- 三个页面没有 `recognition.py` 是有意的，因为它们没有页面专属 OCR；若以后新增 OCR，
  再按本规范创建该文件。
- `bath_page` 既有上下文/OCR、私有 OCR API 和宽泛异常处理问题不属于本批实现范围。

## 9. B1：真实母港主页重塑

本阶段将真实母港 Controller 命名为 `home`，业务状态统一为 `PageName.HOME`。
页面结构为：

`text
controller/home/
├── __init__.py
├── constants.py
├── page.py
├── overlays.py
└── event_nav.py
`

- `controller.py` 改名为 `page.py`，`MainPage` 改名为 `HomePage`。
- `Target` 归入 `page.py`，`OverlayKind` 归入 `overlays.py`；校准数据不再通过
  `common.calibration` 访问。
- 母港导航坐标、通知红点颜色/容差、主页和新闻勾选像素签名已放入
  `home/constants.py`，全部坐标为四位 `0.xxxx` 归一化值，并带业务注释。
- `overlays.py` 和 `event_nav.py` 有运行时真实调用方，继续保留；主页没有 OCR
  专属规则，因此没有创建空 `recognition.py`。
- 生产、导航、业务、测试、工具和直接文档调用方已同步到 `HomePage`；
  `PageName.HOME`、`Templates.MainPage` 和测试目录名保持兼容。
- `bath_page` 未在本阶段修改。

## 10. B1 Ponytail 审查

- 没有发现应删除的新增 Manager、Factory、Registry、兼容别名或重复页面包装。
- `Target`、`OverlayKind`、主页实例包装、浮层分发和活动导航都有真实调用方，
  没有为目录形式制造空模块。
- `event_nav.navigate_to_event(..., is_base_page=...)` 仍保留一个未使用的兼容参数；
  它来自既有调用签名，待确认仓库外消费者后再决定是否删除。
- 这是结构/命名迁移，不处理既有浮层重试策略、上下文所有权或 OCR 私有 API 问题。

## 11. B1 验证与剩余风险

| 检查 | 结果 |
|---|---|
| 主页及直接调用方 AST | 通过，累计解析 173 个 Python 文件 |
| 定向 compileall | 通过 |
| 旧 Controller 路径/主页旧方法扫描 | 通过；剩余 MainPage 仅为视觉资源类名 |
| 主页及直接调用方行宽检查 | 通过；registry.py 文件说明仍有既有超宽行 |
| git diff --check | 通过 |
| Ruff | 未通过：环境没有 ruff 可执行文件 |
| focused pytest | 通过：浮层、初始化和启动相关测试 22 passed |
| runtime import smoke | 通过：home 公共入口、constants、overlays、event_nav 导入成功 |
| 模拟器/实机 E2E | 未执行：当前没有设备验证条件 |

本阶段保留 `main.yaml`、`colors/main.yaml` 和 `signatures/main.yaml`，因为通用校准
接口测试及潜在仓外调用仍依赖其兼容路径；Controller 已不读取这些文件，后续需避免
两套校准值长期漂移。

## 12. B2：母港主页目录名简化

- 类名 `HomePage` 与现有 `MapPage`、`MissionPage`、`BackyardPage`、`SidebarPage`
  的“业务名 + Page”模式一致，无需改名。
- 最终 Controller 包路径为 `application/ui/controller/home/`；仅目录从
  `home_page` 改为 `home`，`page.py`、`constants.py`、`overlays.py`、
  `event_nav.py` 和 `__init__.py` 内容职责保持不变。
- 所有生产、测试、工具、文档和任务记录中的当前包路径已同步；`PageName.HOME`、
  `Templates.MainPage` 和测试目录名保持兼容。
- B2 验证通过：`home` import smoke、22 个 focused pytest、AST 173 文件、
  compileall、旧路径扫描、`git diff --check`、缓存差异检查和绑定验证。
- B2 未新增上下文/OCR 问题，也未修改 `bath_page`。

## 13. B3：主页面状态命名统一

- 将页面枚举成员从 `PageName.MAIN` 统一为 `PageName.HOME`，枚举值仍为
  `主页面`，不改变识别结果、日志字符串或外部字符串契约。
- 已同步导航注册、导航图、运行时、业务、测试、工具、文档和页面栈测试中的
  所有调用方；`HomePage`、`Templates.MainPage` 和模板成员名保持不变。

## 14. B4：按战斗模式移植澡堂导航

交接源 worktree 使用旧的 `autowsgr/ops`、`autowsgr/ui` 架构，未直接合并或
修改源 worktree；行为已按当前分支边界适配到：

- `application/ui/navigation/service.py`：公开普通出征和决战到澡堂的显式路线。
- `application/ui/navigation/__init__.py`：公开导出两条路线。
- `testing/ops/test_bath_navigation.py`：普通/决战路线及“禁止撤退清档”的专项测试。

路线约束：

- 普通出征：`BATTLE_PREP` 先调用 `BattlePreparationPage.go_back()` 回普通
  `MAP`，再沿既有 `MAP → HOME → BACKYARD → BATH` 路线。
- 决战：回到决战地图，打开退出浮层，必须调用 `confirm_leave()` 保存进度，
  禁止调用会清空进度的 `confirm_retreat()`；确认回到决战总览后再进入澡堂。
- 删除无法区分来源的通用 `BATTLE_PREP → MAP` 图边；活动出征
  `BATTLE_PREP → EVENT_MAP` 仍只保留 TODO，未在本批实现。

验证：`97 passed`；定向 compileall、AST、旧状态/旧路径扫描、双侧
`git diff --check` 和 Agent binding verification 均通过。源 worktree 未修改，
GUI 未修改，`bath_page` 未修改。

## 15. B5：页面导航动作命名统一

- `go_home_page()` 现在表示运行时回到 `PageName.HOME` 的母港主页。
- `HomePage.go_to_backyard()` 现在表示从母港进入 `PageName.BACKYARD`；
  `HomePage.go_to_sidebar()` 表示进入 `PageName.SIDEBAR`。
- `HomePage.Target.HOME` 已改为 `HomePage.Target.BACKYARD`，修正了旧名称把
  后院误称为 home 的问题。
- 运行时的 `is_on_home_page()`、`recover_to_home_or_restart()`、
  `_is_on_home_page()` 和 `_wait_for_home_page()` 同步采用 home 语义。
- 未修改公开页面字符串值、`Templates.MainPage`、源 worktree、GUI 或 `bath_page`。
- 验证通过：`97 passed`、semantic import smoke、AST/compile、旧名称扫描和
  `git diff --check`。
