# 第一轮顶层代码治理

日期：2026-09-05
范围：`autowsgr` 顶层目录职责归位，不重写业务行为。

## 当前顶层

```text
autowsgr/
├── server/       外部 HTTP、WebSocket、CLI 和系统入口适配
├── dispatch/     Processor、任务注册、任务队列和触发器
├── business/     可调度业务用例、领域规则和业务结果
├── application/  页面语义、导航、战斗引擎和运行时上下文
└── common/       设备、视觉、系统、校准、契约和只读包资源
```

包根 `__init__.py` 保留版本信息；原全局枚举模块已归入
`common/types.py`。

## 旧目录归位

| 旧目录 | 当前归属 | 第一轮处理 |
|---|---|---|
| `infra/combat` | `application/combat`、`business/combat` | 删除兼容别名，保留实际实现 |
| `infra/emulator` | `common/device` | 删除兼容别名 |
| `infra/system` | `common/system` | 删除兼容别名 |
| `infra/vision` | `common/vision` | 删除兼容别名 |
| `infra/ui/profile` | `common/calibration` | 删除兼容别名 |
| `infra/ui/interaction` | `common/ui/interaction` | 删除兼容别名 |
| `infra/ui/navigation` | `application/ui/navigation` | 删除兼容别名 |
| `infra/runtime/context` | `application/runtime/context` | 移动运行时状态模型 |
| `ui` | `application/ui/legacy` | 兼容页面集中到 application，不再是顶层层级 |
| `ops/normal_fight.py`, `ops/event_fight.py` | `business/combat/bettle` | 普通/活动出征归入同一战斗业务组 |
| `ops/campaign.py` | `business/combat/campaign/compat.py` | 旧战役入口与新战役执行器同域管理 |
| `ops/build.py`, `ops/cook.py`, `ops/destroy.py` | `business/logistics` | 港区操作归入后勤业务域 |
| `ops/startup.py` | `application/runtime/startup.py` | 移动运行时启动/恢复能力 |
| `business/system/initialize` | `application/runtime/initialize` | 移动任务初始化和浮层处理能力 |
| `scheduler/launcher.py` | `application/runtime/launcher.py` | 移动 RuntimeHost 能力 |
| `scheduler/{scheduler,triggers,daily_plan}.py` | `dispatch/legacy_scheduler` | 归入调度层的迁移期旧队列 |
| `constants` | `common/constants` | 移动舰名公共数据 |
| `contracts` | `common/contracts` | 移动 native 舰种契约 |
| `types.py` | `common/types.py` | 移动共享枚举和值类型 |

## 依赖方向

```text
server -> dispatch -> business -> application -> common
```

- `server` 只适配外部请求和结果。
- `dispatch` 只管理任务生命周期和调度，不实现页面或业务步骤。
- `business` 只编排业务用例，可请求 application 能力。
- `application` 提供页面、导航、战斗和运行时语义能力，不决定任务优先级。
- `common` 不依赖项目上层，不知道任务类型和业务状态。

业务包不反向导入 `dispatch`。任务暂停和停止异常定义在
`common/contracts/task.py`，由 `dispatch` 捕获并对外转发；执行器由
`dispatch/registry.py` 的显式映射按需加载，业务模块导入不会修改调度状态。
跨页面导航统一使用 `application/ui/navigation`，不再保留业务层导航转发包。

## 迁移期说明

- `application/ui/legacy`、`dispatch/legacy_scheduler` 是迁移期归档位置，不是新的
  架构层；后续按业务逐个删除或重写。
- 新业务不得从 legacy 包取实现。已迁移的演习、战役和决战入口使用 business 下的
  Executor；决战旧状态机已位于 `business/combat/decisive`。
- 战斗共享的编队解析位于 `business/combat/fleet.py`，跨域编队策略位于
  `business/fleet_policy.py`；不再使用额外的 `combat/fleet` 包层。
- `BaseExecutor` 位于 `application/runtime/executor.py`，战斗历史和通用阶段处理
  位于 `application/combat`；`business/combat` 只保留业务规则和场景决策。
- 普通出征和活动战统一由 `business/combat/bettle/executor.py` 进入，
  `task_type` 决定普通地图或活动地图导航；旧便捷函数仅保留兼容调用。
- 本轮不细拆页面内部职责，不改变 GUI 契约，也不重做普通出征、活动战和后勤业务。
