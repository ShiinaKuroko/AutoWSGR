# AutoWSGR 上下文问题汇总

状态：`TODO`，延期到上下文调试专题集中处理。

所属任务：`20260830-sakuya-exercise-consolidated-7a6c`

## 本次审查结论

本次只记录上下文/OCR 生命周期问题，不修改 `bath_page` 生产代码。

- Bath 专用坐标、颜色和 OCR 参数继续留在
  `application/ui/controller/bath_page/constants.py`。该模块已经私有化这些
  常量并限定模块内调用，本项审查结论为否决修改。
- `BathPage(ctx)` 接收运行中的 `GameContext`，本身不负责创建或刷新上下文。
- 上下文/OCR 问题延期到独立的上下文调试专题，不在本次页面模块审查中增加
  临时兼容层或局部修补。

## 待处理问题

### BathPage 重新创建 OCR，绕过 GameContext

位置：`AutoWSGR/autowsgr/application/ui/controller/bath_page/page.py:366`

当前 `BathPage.recognize_repair_ships()` 的行为：

1. 页面控制器已经保存调用方传入的 `ctx`。
2. `recognize_repair_ships()` 又导入 `OCREngine` 并调用
   `OCREngine.create()` 创建新的 OCR 实例。
3. 新实例被传给 `recognition.recognize_repair_cards()`，没有使用
   `ctx.ocr`。

这会造成页面控制器绕过运行时上下文的 OCR 所有权，潜在影响包括：

- 启动器注入的 OCR 引擎、配置和测试替身无法沿调用链复用；
- OCR 引擎的创建、配置和生命周期可能出现重复来源；
- 页面识别行为与其他通过 `ctx.ocr` 读取 OCR 的页面不一致；
- 单元测试可能只验证页面逻辑，却无法验证实际使用的是上下文中的 OCR。

## 上下文专题处理范围

后续调试专题需要先确认以下事实，再决定最小修改：

- `GameContext.ocr` 的唯一创建者、注入时机和生命周期；
- `BathPage` 是否应直接使用 `ctx.ocr`，以及 OCR 缺失时的明确失败行为；
- `recognize_repair_cards()` 的 OCR 参数是否始终来自运行时上下文；
- 测试如何注入 OCR 替身并断言没有隐式创建新引擎；
- OCR 引擎释放、复用和配置变更是否由上下文统一负责。

建议验收证据：用注入的 OCR 测试替身调用
`BathPage.recognize_repair_ships()`，证明识别函数收到的就是
`ctx.ocr`；同时覆盖 OCR 不可用时的确定性错误路径。

## 本次不处理

以下审查项不属于本 TODO 的上下文专题范围，本次不做未经确认的修改：

- `recognition.py` 的宽泛 `except Exception`；
- `repair_longest` 的命名与跨页面最长修理选择语义；
- 对 `common.vision.ocr._fuzzy_match` 私有 API 的依赖；
- 两套浮层关闭等待逻辑的差异。

这些问题仍保留为独立审查结论，后续按单独任务决定是否修复。

## 2026-09-07 UI Controller 样板审查

- 本批重写的 `build_page`、`backyard_page` 和 `canteen_page` 不拥有 OCR 逻辑，
  未新增上下文/OCR 生命周期问题。
- 既有 `BathPage` 的 `ctx.ocr` 绕过问题仍按本文件延期，不在本批次处理。

## 2026-09-08 Home Page 审查

- `HomePage` 只保存调用方注入的上下文并使用 `ctx.ctrl`，没有创建或刷新
  `GameContext`，本次未发现新的上下文/OCR 生命周期问题。
- 主页没有页面专属 OCR 规则，因此没有新增识别入口；既有 BathPage 上下文问题
  仍按本台账延期，不因主页迁移提前处理。
