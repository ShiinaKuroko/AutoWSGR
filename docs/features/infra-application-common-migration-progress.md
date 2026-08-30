# infra application/common 迁移进度

任务书：`update/infra-application-common-migration-task.md`
分支：`codex/20260830-sakuya-exercise-consolidated-7a6c`

## 进度

- CP0：完成。基线 `78acc7a`，保留用户 dirty diff。
- CP1：完成。提交 `234c11a`，两个正式 package 可导入。
- CP2：进行中。`common/system` 已迁移，设备和视觉待处理。
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
