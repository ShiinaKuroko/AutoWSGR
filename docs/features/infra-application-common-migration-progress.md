# infra application/common 迁移进度

任务书：`update/infra-application-common-migration-task.md`
分支：`codex/20260830-sakuya-exercise-consolidated-7a6c`

## 进度

- CP0：完成。基线 `78acc7a`，保留用户 dirty diff。
- CP1：完成。提交 `234c11a`，两个正式 package 可导入。
- CP2：完成。`common/system`、`common/device`、`common/vision`、`common/calibration`、`common/ui` 和只读资源已迁移。
- CP3：进行中。语义导航和页面动作待迁移到 application。
- CP3-CP7：待执行。

## 约束

- `autowsgr/business/combat/exercise/operations.py` 的用户修改不属于本任务，不暂存、不回退。
- 不追加真实设备 E2E；已有 `logs/e2e_tools/exercise/20260830_220134` 作为证据。
- pytest 延后到迁移和静态检查完成后最后统一执行。

## CP2 记录

迁移判据：common 只返回基础类型、common 自有类型或技术识别结果；依赖
 GameContext、PageName、业务规则或上层包的模块留在 application/business，
或先拆出低层子模块。

## CP2a：common/system

- 实现 canonical 路径：`autowsgr/common/system/`。
- 旧路径 `autowsgr/infra/system/` 仅保留 re-export shim。
- 配置、异常、YAML 文件工具和日志没有导入 application、business、dispatch 或 server。
- 检查：导入 smoke、compileall、Ruff check/format、`git diff --check` 通过。

## CP2b：common/device 和 common/data

- 实现 canonical 路径：`autowsgr/common/device/`。
- 设备连接、截图、触控、ADB 探测和宿主模拟器进程管理只依赖 common/system、types 和底层库。
- 只读资源从 `autowsgr/infra/data/` 移至 `autowsgr/common/data/`，不保留资源副本。
- 旧 `autowsgr/infra/emulator/` 路径通过同一实现的 module alias 保持可用。
- 检查：canonical/legacy 导入 smoke、compileall、Ruff check/format、`git diff --check` 通过。

## CP2c：common/vision

- 实现 canonical 路径：`autowsgr/common/vision/`。
- OCR、OpenCV、ROI、像素/模板匹配和资源索引不导入 application、business、dispatch 或 server。
- 旧 `autowsgr/infra/vision/` 路径通过子模块 alias 指向 canonical 实现，避免 patch 点和实现分叉。
- 检查：canonical/legacy 导入 smoke、compileall、Ruff check/format、`git diff --check` 通过。

## CP2d：common/ui 和 common/calibration

- 低层点击、等待、确认和校准加载器分别位于 `autowsgr/common/ui/`、`autowsgr/common/calibration/`。
- 等待函数不再导入页面 registry；页面语义由 application Navigator 负责。
- 旧 `autowsgr/infra/ui/interaction.py` 和 `infra/ui/profile/*` 仅指向 canonical 模块。
- 检查：canonical/legacy 导入 smoke、坐标读取、compileall、Ruff check/format、`git diff --check` 通过。
