# AutoWSGR 架构概述

本文档面向框架开发者，描述 AutoWSGR 后端的整体架构、分层设计与核心数据流。

> **用户使用文档** 见 [docs/usage/](../usage/)。

---

## 分层架构

```
┌─────────────────────────────────────────────────────┐
│  server             HTTP / CLI / Timer 适配           │
├─────────────────────────────────────────────────────┤
│  dispatch           Processor、队列、任务生命周期     │
├─────────────────────────────────────────────────────┤
│  business           可调度业务 Executor               │
├─────────────────────────────────────────────────────┤
│  application        页面、导航、战斗引擎、运行时能力   │
├─────────────────────────────────────────────────────┤
│  common             设备、视觉、系统、校准、包资源     │
└─────────────────────────────────────────────────────┘
```

代码依赖只能向下；结果、检查点和事件向上返回。`GameContext` 是迁移期旧聚合，
新代码使用明确的运行时能力和类型化契约，不把设备、导航和任务状态重新集中进去。

| 层            | 包路径                | 职责                            | 细节文档                                     |
|---------------|----------------------|---------------------------------|----------------------------------------------|
| **server**    | `autowsgr/server/`    | HTTP、WebSocket、CLI 和运行时入口适配       | [scheduler-and-server.md](scheduler-and-server.md) |
| **dispatch**  | `autowsgr/dispatch/`  | Processor、任务队列和生命周期               | [scheduler-and-server.md](scheduler-and-server.md) |
| **business**  | `autowsgr/business/`  | 可调度业务用例、领域规则和执行器             | [ops.md](ops.md)                             |
| **application** | `autowsgr/application/` | 页面语义、导航、战斗引擎和运行时上下文     | [layer-governance-round1.md](layer-governance-round1.md) |
| **common**    | `autowsgr/common/`    | 设备、视觉、系统、校准、契约和只读包资源     | [layer-governance-round1.md](layer-governance-round1.md) |

当前顶层目录治理和旧路径归位见
[第一轮治理索引](layer-governance-round1.md)。`infra`、`ops`、`ui`、`scheduler`、
`constants`、`contracts` 已不再是现行架构层级；相关旧文档中的路径仅作历史参考。

---

## 核心数据流

一次典型的"启动 → 战斗 → 收集结果"流程：

```
usersettings.yaml
       │
       ▼
  ConfigManager.load()          # YAML → Pydantic 校验 → UserConfig
       │
       ▼
  Launcher / server adapter
       ▼
  Processor                   # 创建 TaskInstance、调度和控制
       ▼
  BusinessExecutor            # 业务步骤和检查点
    ├─ Navigator               # 语义页面交接
    ├─ BattlePreparationPage   # 出征准备和编队
    └─ CombatEngine.fight()    # 战斗基建状态机循环
         │
         ├─ CombatRecognizer.wait_for_phase()  # 截图 → 模板+像素匹配 → 阶段
         ├─ PhaseHandler._handle_*()           # 阶段处理 (操作 + 决策)
         └─ CombatResult                       # 战果、血量、掉落
       │
       ▼
  TaskScheduler / HTTP API      # 多任务调度 / 外部接口
```

---

## 关键设计原则

### 1. 运行时能力注入

`GameContext` 仍是迁移期旧聚合，只允许作为上层业务的临时承载。战斗基建接收明确的
设备、OCR 和停止查询能力，不再把任务状态或游戏快照带入引擎。

```python
@dataclass
class GameContext:
    # 迁移期模型；新基建不直接依赖它
    ctrl: AndroidController     # 设备控制器
    config: UserConfig          # 用户配置 (只读)
    ocr: OCREngine              # OCR 引擎
    resources: Resources        # 迁移期运行时资源
    fleets: list[Fleet]         # 运行时: 舰队 (1-4)
    ...
```

### 2. 无状态操作

- **UI 页面类**：静态方法 `is_current_page(screen)` 做识别，实例方法做操作
- **战斗 action 函数**：纯函数 `(device, data) -> None`，无副作用
- **Ops Runner**：可重复实例化，每次 `run()` 独立执行

### 3. YAML 驱动配置

- 用户配置：`usersettings.yaml` → Pydantic `UserConfig`
- 作战计划：`infra/data/plan/*.yaml` → `CombatPlan` + `NodeDecision`
- 地图数据：`infra/data/map/*.yaml` → `MapNodeData`

### 4. 状态机模式

战斗引擎核心是 `CombatPhase` 状态机，转移图由 `build_transitions(ModeCategory, end_page)` 动态构建。每步循环：截图 → 识别阶段 → 查转移表 → 执行处理器 → 返回标志位。

### 5. 懒加载

- `LazyTemplate`：图像模板在首次访问时从磁盘加载
- `OCREngine`：由 `Launcher` 按需创建
- 模块级延迟导入：UI 导航动作函数内部 import 页面类，避免循环依赖

---

## 当前项目目录

```
autowsgr/
├── server/                  # HTTP、WebSocket、CLI 和外部入口适配
├── dispatch/                # Processor、请求准入、队列和生命周期
├── business/                # 可调度业务用例和领域规则
├── application/             # 页面、导航、战斗和运行时应用能力
└── common/                  # 设备、视觉、系统、契约和只读包资源
```

目录内的依赖只能向下：`server -> dispatch -> business -> application -> common`。
旧目录树保留在下方仅供历史文档对照。

---

## 历史目录（已废弃）

```
autowsgr/
├── __init__.py              # 版本号 (__version__)
├── types.py                 # 全局枚举 (OSType, ShipType, Formation, ...)
├── constants/               # 舰船名数据库 (SHIPNAMES)
├── infra/                   # 配置、日志、异常、文件工具
│   ├── config.py            #   UserConfig Pydantic 模型层级
│   ├── logger.py            #   loguru 通道日志系统
│   ├── exceptions.py        #   异常层级树
│   └── file_utils.py        #   YAML/路径工具
├── emulator/                # 模拟器连接层
│   ├── controller/          #   ScrcpyController (AndroidController 实现)
│   ├── os_control/          #   进程管理 (Windows/Mac/Linux)
│   └── detector.py          #   设备自动检测
├── vision/                  # 视觉识别
│   ├── pixel.py             #   像素特征数据模型
│   ├── matcher.py           #   PixelChecker 引擎
│   ├── image_matcher.py     #   ImageChecker 模板匹配引擎
│   ├── ocr.py               #   OCREngine 抽象 + EasyOCR
│   ├── roi.py               #   ROI 区域定义
│   └── image_template.py    #   ImageTemplate 数据模型
├── image_resources/         # 图像模板资源
│   ├── keys.py              #   TemplateKey 枚举
│   ├── combat.py            #   CombatTemplates (战斗模板)
│   ├── ops.py               #   Templates (操作模板)
│   └── _lazy.py             #   LazyTemplate 懒加载
├── ui/                      # UI 页面系统
│   ├── page.py              #   页面注册中心
│   ├── navigation.py        #   导航图 + BFS 寻路
│   ├── utils.py             #   等待/点击工具
│   ├── main_page.py         #   主页面
│   ├── map/                 #   地图页面
│   ├── battle/              #   出征准备页
│   ├── decisive/            #   决战 UI
│   └── ...                  #   其他页面
├── combat/                  # 战斗引擎
│   ├── engine.py            #   CombatEngine 状态机主循环
│   ├── state.py             #   CombatPhase 枚举 + 转移图
│   ├── plan.py              #   CombatPlan + NodeDecision + CombatMode
│   ├── handlers.py          #   PhaseHandlersMixin (阶段处理器)
│   ├── recognizer.py        #   CombatRecognizer (视觉识别器)
│   ├── recognition.py       #   敌舰/阵型/掉落识别
│   ├── actions.py           #   战斗操作函数 (点击/检测)
│   ├── rules.py             #   RuleEngine (索敌规则)
│   ├── history.py           #   CombatHistory + CombatResult
│   └── node_tracker.py      #   MapNodeData + NodeTracker
├── business/                # 可调度业务用例
│   └── combat/campaign/     #   CampaignExecutor 战役链路
├── ops/                     # 游戏操作
│   ├── normal_fight.py      #   NormalFightRunner
│   ├── campaign.py          #   CampaignRunner 兼容入口
│   ├── exercise.py          #   ExerciseRunner
│   ├── event_fight.py       #   EventFightRunner
│   ├── decisive/            #   DecisiveController
│   ├── startup.py           #   启动/重启游戏
│   ├── navigate.py          #   goto_page / identify_current_page
│   ├── repair.py            #   澡堂修理
│   ├── expedition.py        #   远征收取
│   ├── build.py             #   建造/收船
│   ├── cook.py              #   食堂烹饪
│   ├── destroy.py           #   解装
│   └── supply.py            #   补给
├── context/                 # 游戏上下文
│   ├── game_context.py      #   GameContext 核心类
│   ├── fleet.py             #   Fleet 模型
│   ├── ship.py              #   Ship 模型
│   ├── resources.py         #   Resources 模型
│   ├── expedition.py        #   ExpeditionQueue
│   └── build.py             #   BuildQueue
├── scheduler/               # 调度器
│   ├── launcher.py          #   Launcher 启动链 + launch()
│   └── scheduler.py         #   TaskScheduler
├── server/                  # HTTP 服务
│   ├── main.py              #   FastAPI 应用
│   ├── task_manager.py      #   TaskManager
│   ├── ws_manager.py        #   WebSocket 管理
│   ├── schemas.py           #   请求/响应模型
│   └── routes/              #   路由模块
└── data/                    # 静态数据
    ├── missions.yaml        #   任务数据库
    ├── shipnames.yaml       #   舰船图鉴
    ├── images/              #   模板图片
    ├── map/                 #   地图节点数据
    ├── plan/                #   作战计划 (YAML)
    └── bin/                 #   二进制资源 (scrcpy-server 等)
```

---

## 细节文档索引

| 文档                                                | 内容                                               |
|-----------------------------------------------------|----------------------------------------------------|
| [context-and-config.md](context-and-config.md)      | GameContext 结构、UserConfig 模型层级、配置加载流程    |
| [emulator.md](emulator.md)                          | AndroidController 协议、ScrcpyController、设备检测   |
| [vision.md](vision.md)                              | 三层视觉栈（像素/模板/OCR）、图像资源管理             |
| [ui.md](ui.md)                                      | 页面注册中心、导航图 BFS、页面控制器                   |
| [combat-engine.md](combat-engine.md)                | 战斗状态机、CombatPlan、阶段处理器、视觉识别器         |
| [ops.md](ops.md)                                    | 战斗 Runner、非战斗操作、启动与导航                   |
| [scheduler-and-server.md](scheduler-and-server.md)  | Launcher 启动链、TaskScheduler、FastAPI HTTP 服务     |
| [infra.md](infra.md)                                | 通道日志、异常层级、文件工具、枚举类型、数据文件        |
| [code-graph.md](code-graph.md)                      | 静态架构图谱、层级检查、动态关系和重构差异             |
