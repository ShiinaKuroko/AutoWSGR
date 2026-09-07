# UI Controller 样板与三模块重构任务书

Task ID: `20260830-autowsgr-upgrade`
Task Status: `done`
Next Step: 等待人工 review。

## 工作目标

以当前 `bath_page` 的职责划分为参考，建立统一的 UI Controller 页面模块
规范，并按规范重写 `build_page`、`backyard_page`、`canteen_page`。同时修复
已经确认的浴室浮层关闭状态判断问题，最后产出可供人工 review 的综合报告。

## 固定工作位置

- Meta：`C:\ShiinaKuroko\01.Project\AutoWSGR\.worktrees\20260830-autowsgr-upgrade\meta`
- AutoWSGR：`C:\ShiinaKuroko\01.Project\AutoWSGR\.worktrees\20260830-autowsgr-upgrade`
- 分支：`codex/20260830-autowsgr-upgrade`
- 原则：所有代码和文档修改只发生在上述绑定 worktree；原始物理副本不写入。

## 交付边界

- `bath_page` 只允许 A1 为修复关闭状态确认而做最小修改。
- 禁止为了套用新样板而重写、搬迁、格式化或清理 `bath_page`。
- 不新增依赖、兼容层、第二套状态源或未经调用方证明必要的抽象。
- 不处理已经登记的上下文/OCR 专题；相关发现只写入对应 `[todo]` 台账。
- pytest 不作为本任务的单独目标或阻塞条件；必要的静态检查、导入检查和可重复 smoke 仍需记录。

## 阶段与完成标准

### A1：修复浮层关闭状态确认（已完成）

- 保留三种业务语义：主动关闭导航、选船后判断修理结果、全部修理后的收尾。
- 所有“关闭成功”路径必须有明确的最终状态确认：浮层消失，并在需要时确认仍处于浴室页面。
- 全部修理的手动关闭不能只点击后睡眠再返回，必须确认点击生效；失败应保留可见错误终态。
- 只修改 `bath_page` 完成本项所需的最小代码和必要记录。
- 完成后检查 diff、运行最小可重复验证，并重读本任务书。

### A2：提炼 UI Controller 样板（已完成）

- 先完整阅读 `[规范]navigation-code-style.md`，按其中的注释分类划分规则。
- 以当前 `bath_page` 的有效职责为参考，区分页面操作、物理校准和 OCR 识别。
- 明确页面模块的统一目录、文件职责、函数前缀和函数排序规则。
- 明确常量注释必须表达业务语义；点击坐标使用 `0.xxxx` 相对格式。
- 完成后重读本任务书。

### A3：编写规范文件（已完成）

- 新文件：`[规范]ui-controller-code-style.md`。
- 内容必须覆盖：
  - `xx_page/` 目录结构；
  - 私有 `constants.py` 的上下文/校准边界；
  - `page.py` 的 UI 操作规则；
  - `recognition.py` 的 OCR 专属边界；
  - 注释类别、点击坐标、业务语义注释；
  - `check`、`open`、`click` 等动作前缀统一要求；
  - `def` 排序规则；
  - 不适用某文件时的最小处理方式；
  - 验证和禁止事项。
- 规范必须以当前代码真实调用方式为依据，不反向要求 `bath_page` 迁移。
- 完成后重读本任务书。

### A4：按规范重写三个页面模块

- 目标模块：`build_page`、`backyard_page`、`canteen_page`。
- 修改前必须盘点每个模块的导入方、调用方、公共 API、页面导航和测试。
- 每个模块按规范拆分为 `constants.py`、`page.py`、`recognition.py`；若某模块没有 OCR 逻辑，记录理由并采用最小目录形态，不制造空壳代码。
- 保持现有业务行为、公共导入路径、页面导航和配置契约；必要的导入适配必须同步检查全部调用方。
- 仅迁移真实属于目标模块的职责；发现边界扩展超出三个模块时暂停并记录，不顺手扩散。
- 每完成一个页面模块：检查该模块 diff、执行匹配验证，然后重读本任务书再开始下一个模块。
- [x] `build_page` 已完成目录拆分、坐标私有化和调用方命名同步。
- [x] `backyard_page` 已完成目录拆分、坐标私有化和调用方命名同步。
- [x] `canteen_page` 已完成目录拆分、坐标私有化和调用方命名同步。
- 三个模块全部完成后重读本任务书。

### A5：Ponytail 审查与问题归档（已完成）

- 使用 `ponytail` 对本批代码做过度设计审查，重点检查重复抽象、无调用方接口、重复常量和无必要兼容层。
- 与上下文或 OCR 相关的问题写入已有或新建的 `[todo]` 台账，不在本批次扩展修复范围。
- 其他问题写入综合报告，不隐藏未解决项，不用 fallback 掩盖问题。
- 完成后重读本任务书。

### A6：综合报告（已完成）

- 新文件建议命名：`[报告]ui-controller样板重构综合报告.md`。
- 报告包含：目标和边界、变更文件、A1 修复说明、三模块重构说明、验证命令与结果、Ponytail 审查结果、`[todo]` 台账、未完成项和剩余风险。
- 报告不得宣称未执行的 pytest、实机或全量检查已通过。
- 完成后重读本任务书，并将 Task Status 更新为 `done`（若仍有必须处理的任务则保持 `in_progress` 并写明 Next Step）。

### B1：真实母港主页重塑（已完成）

- 将 Controller 目录从 `controller/main_page` 重命名为 `controller/home_page`。
- 将 Controller 文件从 `controller.py` 规范为 `page.py`，并将 `MainPage` 重命名为 `HomePage`。
- 保留业务状态 `PageName.HOME` 和视觉资源 `Templates.MainPage`，同步所有仓内调用方。
- 将主页实际使用的坐标、颜色和像素签名下沉到页面私有 `constants.py`；
  保留通用 `main.yaml` 校准兼容数据，不修改 `bath_page`。
- 浮层和活动导航继续保留为真实依赖模块，分别按规范使用绝对导入和统一状态前缀。
- 已重读本任务书，完成 AST/compile、focused 验证、旧路径扫描和 `git diff --check`；
  Task Status 更新为 `done`，等待人工 review。

### B2：母港主页目录名简化（已完成）

- `HomePage` 类名符合其他页面的“业务名 + Page”命名约定。
- 将 Controller 目录从 `controller/home_page` 简化为 `controller/home`。
- 保留 `HomePage`、`PageName.HOME`、`Templates.MainPage` 和页面内部文件结构。
- 已重读本任务书，完成 import smoke、focused pytest、AST/compile 和
  `git diff --check`；Task Status 更新为 `done`，等待人工 review。

### B3：主页面状态命名统一（已完成）

- 业务状态统一使用 `PageName.HOME`，值继续保持“主页面”；已同步全部仓内调用方。
- 同步导航、运行时、业务、测试、工具和文档调用方。
- 保留 `Templates.MainPage`、`HomePage` 和外部页面字符串契约。

### B4：按战斗模式移植澡堂导航（已完成）

- 普通出征准备页必须先通过 `BattlePreparationPage.go_back()` 回到普通地图，
  再走既有地图 → 主页 → 后院 → 浴室路线。
- 决战出征准备页必须回到决战地图，打开退出浮层并使用 `confirm_leave()` 保存进度；
  禁止使用 `confirm_retreat()`，之后确认回到决战总览再进入澡堂。
- 删除无来源区分的通用 `BATTLE_PREP -> MAP` 图边；活动出征返回路线只记录 TODO。
- 已重读本任务书，完成 focused pytest、AST/compile 和 `git diff --check`；
  Task Status 保持 `done`，等待人工 review。

### B5：页面导航动作命名统一（已完成）

- 运行时回母港主页使用 `go_home_page`，不再使用语义过时的 `go_main_page`。
- 主页进入后院使用 `go_to_backyard`，进入侧边栏使用 `go_to_sidebar`。
- 主页导航目标使用 `Target.BACKYARD`，不再用 `Target.HOME` 表示后院。
- 已重读本任务书，完成 focused pytest、AST/compile 和 `git diff --check`；
  Task Status 更新为 `done`，等待人工 review。

## 每阶段强制重读协议

每完成一项或一个页面模块，执行：

```powershell
Get-Content -Encoding UTF8 -Raw -LiteralPath 'C:\ShiinaKuroko\01.Project\AutoWSGR\.worktrees\20260830-autowsgr-upgrade\meta\[任务书]ui-controller样板重构任务.md'
```

重读后才允许进入下一阶段。若任务书与当前代码、用户新决定或验证结果冲突，
立即停在当前阶段，先更新任务书并记录冲突，不继续实现。

## 记录要求

- 每次阶段完成后更新 `progress.md`；重要发现写入 `findings.md`。
- 所有失败命令、失败原因和替代验证写入 `progress.md`，不得重复同一失败尝试。
- 交付前检查 `git diff --check`，并确认 AutoWSGR diff 不包含无关文件。
