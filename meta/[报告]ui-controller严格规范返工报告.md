# UI Controller 严格规范返工报告

状态：`已完成（保留明确 TODO）`，本报告取代此前“Controller 阶段二已完成”的验收结论。

基线：`d1ddffd`，分支 `codex/20260830-autowsgr-upgrade`。

## 返工范围

本次按以下规范重新审查并实际修改当前 worktree：

- `meta/[规范]ui-controller-code-style.md`
- `meta/[规范]navigation-code-style.md`

保留约束：不修改 `backyard/bath_page`，不改写选船算法；OCR、ROI、上下文生命周期
和 OCR 私有 API 只记录到 TODO，未用兼容入口掩盖问题。

## 已落地治理

### 文件和目录

- `controller/battle_preparation/` 已归入
  `controller/operations/sortie_page/battle_preparation_page/`。
- 出征准备页面组合入口 `preparation.py` 改为 `page.py`。
- 顶部标签 Mixin `sortie.py`、`decisive.py` 改为 `sortie_panel.py`、
  `decisive_panel.py`。
- 主页浮层工具 `overlays.py` 改为 `overlay.py`。
- 跨模式选船控制器包化为 `shared/choose_ship_page/page.py`，由包级
  `__init__.py` 提供稳定出口。
- 决战编队策略文件改为 `fleet_change/decisive_fleet.py`，避免与决战页面组混淆。
- 所有当前页面组都具备明确的 `page.py`；有 OCR 规则的页面保留
  `recognition.py`，没有 OCR 的页面未新增空识别文件。

### 命名和编排

- 顶部标签公共入口统一为 `check_tab_bar`、`read_active_tab_index`、
  `read_page_type`、`create_tab_checker` 和 `create_page_checker`。
- 选船页面状态、搜索、键盘、移除和单舰选择入口统一为
  `check_current_page`、`open_search_box`、`dismiss_keyboard`、
  `click_remove_ship`、`select_single_ship`。
- 地图面板区分无条件点击 `click_panel` 与条件选择 `select_panel`。
- 准备页快捷面板统一为 `open_quick_supply`、`open_quick_repair`；侧边栏回退入口为
  `close_sidebar`；决战章节按钮和地图准备页返回入口使用 `click_*`/`navigate_to_*`。
- `BuildPage.go_back` 和解体过滤器方法已按真实流程重新排序；选船私有辅助已移到
  类末尾。
- 当前 Controller 模块均有“模块功能 / 上层调用 / 下层依赖”文件级说明（受保护的
  `backyard/bath_page` 未改动）。
- 页面点击、滑动和 ROI 归一化坐标采用 `0.xxxx`；出征准备舰种 OCR 的高精度裁剪值
  保留原精度，避免未经视觉验证改变像素映射。

## TODO 与未决项

- `shared/choose_ship_page/page.py` 仍混合选船算法、OCR、上下文和共享校准；这是用户
  明确保护的高风险代码，留给 OCR/上下文专题。
- `battle_preparation_page/detection.py`、编队 `_detect.py` 和决战识别仍有 OCR/ROI
  生命周期及 `_fuzzy_match` 私有 API 依赖，已更新到两个 TODO 台账。
- `BathPage` 的 OCR 创建、最长修理命名/选择语义、浮层关闭双路径和 `bath_page` 私有
  API 均未修改，保持原 TODO。
- 选船页面没有独立的 `go_back` 实现，当前通过准备页流程等待离开；导航兼容性只做
  记录，不在本批次增加来源不明的导航边。
- `PageName` 成员语义统一仍按 `meta/[todo]PageName语义统一.md` 延后。

## 验证证据

- Controller、导航、业务和应用相关目录 `compileall`：通过。
- 新目录、包级导出和导航注册 import smoke：通过。
- 结构/旧路径/旧公共 API 静态扫描：通过；受保护 BathPage 排除在修改范围外。
- focused 回归：`364 passed`。
- 受影响文件 pre-commit（包含 Ruff、AST、codespell）：通过。
- `git diff --check`：通过。
- 未执行真实游戏/模拟器 E2E；报告不宣称实机行为已验证。

## 交付边界

本次未执行 commit、merge、cherry-pick、reset、stash、清理或远程操作。当前工作区的
代码与计划文件仍由用户后续 review；严格返工只有在用户确认剩余 TODO 的处理范围后，
才进入 OCR/上下文或 PageName 专题。
