# infra application/common 迁移冲突记录

日期：2026-08-30
任务书：`update/infra-application-common-migration-task.md`
基线：`78acc7a4688703f51e19cd5a42fb04353614bfea`
分支：`codex/20260830-sakuya-exercise-consolidated-7a6c`

## CP0 结果

- backend Git root 已确认。
- 当前工作树存在一处不属于本任务的 dirty diff：
  `autowsgr/business/combat/exercise/operations.py` 删除 3 个空行。
- 未跟踪文件：无。
- `autowsgr/application/` 和 `autowsgr/common/` 目录存在但为空，尚未有 package 文件或实现。
- 本轮未修改 dirty 文件，未运行 pytest。

## 冲突清单

### C1：宏观层级数量

- 纪要：`server -> dispatch -> business/navigation -> infra`，明确“不需要增加更多宏观层级”，见纪要 429-494 行。
- 任务书：要求 `business`、`application`、`common` 与 `server`、`dispatch` 同级，依赖为
  `server -> dispatch -> business -> application -> common`。
- 影响：创建两个正式包即改变顶层依赖图；继续迁移会改变所有 import owner。
- 状态：未执行，等待用户裁定哪一版是当前有效架构。

### C2：Navigator 归属

- 纪要：共享 Navigator 属于 business 的互补导航编排子层，页面/设备能力留在 infra，见纪要 500-558、584-590 行。
- 任务书：语义 Navigator 迁入 `application/ui/navigation`，application 只能依赖 common。
- 影响：涉及 `infra/ui/navigation`、`business` 入口和运行时会话的长期 owner，不能只改路径。
- 状态：未执行。

### C3：CombatEngine 归属

- 纪要：CombatEngine 是 business 层下面的领域引擎/领域服务，推荐位置为 `business/combat/engine`，见纪要 465-468、692-697 行。
- 任务书：通用 CombatEngine/action 迁入 `application/combat`，战斗规则和结果语义留在 business。
- 影响：需要拆分通用动作、战斗规则、结果模型和状态机；直接搬文件会形成 application -> business 或重复模型。
- 状态：未执行。

### C4：物理 UI、OCR 和设备能力归属

- 纪要：页面控制器、页面识别、OCR、模板、设备操作属于 `infra/base/ui`、`infra/vision`、`infra/emulator`，见纪要 623-635、741-755、792-807 行。
- 任务书：OCR、OpenCV、设备连接、低层 UI、校准资源分别迁入 `common` 子包，application 只组合动作。
- 影响：会改变现有演习链路的真实实现来源；必须逐模块确认 common 不反向依赖 GameContext、business 或 application。
- 状态：未执行。

### C5：入口与运行时边界

- 纪要：Processor 选择任务后调用共享 Navigator，Business 再调用同一 Navigator；RuntimeSession 负责设备、OCR、UIProfile 和 lease，见纪要 524-552、961-987 行。
- 任务书：application 提供 Navigator/CombatEngine，common 提供底层资源，但同时要求 CP4 修复 GameContext owner 和 server/dispatch 旁路。
- 影响：在 RuntimeSession、GameContext、Processor 尚未收口前迁移 application/common，会产生双 owner 或跨层 facade。
- 状态：未执行，需先确认是否把任务书视为对纪要的正式修订。

## 暂不构成冲突的事项

- Python 文件格式、Ruff/pre-commit、注释简洁、避免连续空行：按仓库 `.pre-commit-config.yaml` 和 `pyproject.toml` 执行。
- 本任务不追加真实设备 E2E；既有 5/5 预算和 `20260830_220134` 日志保持有效。
- pytest 延后到全部迁移批次和静态检查完成后最后统一执行。

## 待用户确认

请确认 C1-C5 是否按任务书覆盖纪要中的旧归属。确认后从 CP1 开始创建 package 边界，再按调用图迁移；未确认前不移动 `infra`、`business`、Navigator 或 CombatEngine 的实现。

## 用户裁定

2026-08-30：用户确认按新任务书执行，任务书中的 `application/common` 分层覆盖纪要旧归属。C1-C5 不再阻塞后续迁移；冲突记录保留作为历史依据。

## 2026-08-31 执行结果

- C1：按用户裁定执行，`application`/`common` 与 `business` 同级包已建立。
- C2：语义 Navigator 已迁入 `application/ui/navigation`，旧路径为薄 alias。
- C3：通用驱动/动作与业务计划、规则、历史拆分完成；业务结果入口位于
  `business/combat`，application 驱动通过 factory 接收业务结果。
- C4：页面、设备、OCR 基础路径已切换 canonical；战斗识别器仍保留一层
  application 适配，底层 OCR/OpenCV 继续由 `common/vision` 提供。
- C5：运行时类型边界和 alias 作用域已收口；混合 `GameContext` 的完整字段拆分留作后续
  runtime 专项，不复制第二个上下文。

本次执行未追加真实设备 E2E，沿用既有 `logs/e2e_tools/exercise/20260830_220134` 证据。
