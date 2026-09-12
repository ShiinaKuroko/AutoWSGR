# 导航器治理报告

日期：2026-09-05
任务书：`[任务书]navigation-governance-task.md`
范围：`AutoWSGR/autowsgr/application/ui/navigation` 及其直接页面调用方。

## 结论

本轮任务书 1 至 6 项全部完成。导航器的代码结构和注释已统一，导航图仍保持
23 条边和原有页面行为。`application/ui/pages` 已经是业务可调用的 UI application
入口，不新增只有转发作用的 `application/ui/operations.py`。

本次返工将文件头改为业务语言，明确写出调用方、被调用模块和 canonical 路径；函数注释
只说明实际业务动作，不再把包路径堆在每一行。导航目录分区统一使用 `# ── ... ───`，
连续空行最多两行，并以 pre-commit 的实际结果为准。

## 调用链

```text
business Executor
  -> navigation.goto_page(ctx, target)
  -> service._goto_page
  -> recognition.identify_current_page
  -> registry.register_default_pages
  -> page.is_current_page(screen)
  -> UIStack.observe
  -> graph.find_path
  -> UIStack.push
  -> NavEdge.action
  -> application.ui.pages 页面动作
  -> common.ui.interaction 点击并等待
  -> ctx.ctrl.screenshot/click
  -> 页面检查器确认目标页面
```

导航器各模块职责：

| 模块 | 责任 |
|---|---|
| `service.py` | 业务入口、逐步寻路、失败后重建栈并重试 |
| `recognition.py` | 截图识别、匹配结果排序、上下文页面同步 |
| `registry.py` | 页面识别器注册和默认页面装载 |
| `stack.py` | 页面来路、候选页面、漂移标记和栈重建数据 |
| `graph/` | 公共、战斗、后勤导航边和 BFS 路径 |

## common 依赖

导航核心直接依赖：

- `common.types.PageName`：页面名和值类型，位于 graph、recognition。
- `common.vision.page_match.PageMatch`：页面识别统一结果，位于 recognition 和 registry 契约。
- `common.system.logger.get_logger`：导航、识别、栈和注册日志。
- `common.ui.interaction.NavigationError`：导航失败和重试边界。
- `ctx.ctrl.screenshot()`、`ctx.ctrl.click()`：通过运行时控制器契约提供设备能力。

页面动作的间接依赖：

- `common.ui.interaction`：`click_and_wait_for_page`、`wait_for_page`、
  `wait_leave_page`、`confirm_operation`。
- `common.vision`：模板匹配、像素匹配、OCR、`PageMatch` 和资源加载。
- `common.calibration`：点击坐标、探测点、页面区域和签名。
- `common.device`：由 `ctx.ctrl` 实现截图、点击和滑动。
- `common.system`：日志和 UI/动作异常。
- `common.types`：页面、舰船和页面操作状态值。

这些能力都被多个页面或业务复用，继续放在 common；导航专属的路径、栈和页面语义
留在 application，不向 common 下沉。

## 导航与 UI 边界

- 导航器负责“从当前页面到达目标入口或安全锚点”，包括识别当前页面、计算路径、
  执行边动作和确认到达。
- `application/ui/pages` 负责“页面内怎么做”，包括坐标点击、面板切换、页面状态
  读取、等待和页面级校验。
- graph 回调只调用页面控制器语义方法，例如 `MainPage.navigate_to`、
  `MapPage.enter_decisive`、`BattlePreparationPage.go_back`。
- 业务层可以依次调用 `goto_page` 和页面 application 方法，但不应自行拼接
  `common.ui.interaction`、截图和页面识别细节。
- 当前业务仍有少量 common 直调用：`business/logistics/destroy.py` 使用
  `click_and_wait_for_page`；普通出征、战役、演习操作和战斗决策处理器直接使用
  `NavigationError` 或 `wait_leave_page`。这些是后续边界治理项，本轮没有添加空转发层。

## application 入口评估

保留现状。`application/ui/pages` 已提供有业务语义的页面操作入口，新增一个通用
`application/ui/operations.py` 只会重复转发，不能改善依赖方向。

只有出现跨多个页面、需要一个统一状态和结果的真实 UI 流程时，才在 application
增加一个有明确业务语义的方法。底层截图、点击、等待、视觉、校准和设备实现继续由
common 提供。

## 已知后续项

- `common/ui/interaction.py` 仍有第二份 `NavigationError`，且 `candidates`、
  `handle_overlays` 参数没有实际参与识别。
- `confirm_operation` 仍带有 Legacy 行为说明；`click_and_wait_leave_page` 当前没有
 生产调用方。
- `main_page/event_nav.py` 的 `is_base_page`、`map/data.py` 的兼容再导出、
  `battle_preparation/constants.py` 的兼容导出仍待后续专门清理。
- 以上项目不影响本轮导航 graph 和 service 的真实接入，清理时需要逐个检查消费者。

## 验证

```text
pytest -q testing/architecture/test_layer_packages.py \
  testing/business/combat/exercise/test_navigation.py \
  testing/ui/page/test_unit.py testing/ui/page/test_ui_stack_unit.py
48 passed

pre-commit run --files <导航器 9 个 Python 文件>
passed

python -m compileall -q autowsgr/application/ui/navigation autowsgr/application/ui/pages
passed

git diff --check
passed
```

本轮没有执行实机 E2E；任务书明确要求先完成静态治理。本轮 backend 代码提交为
`ae0f989`，承接导航结构提交 `c6173f2` 和注释提交 `ae517f7`；meta 计划和本报告另行记录。
