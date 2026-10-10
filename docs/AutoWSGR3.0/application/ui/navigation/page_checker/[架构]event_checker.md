# application-ui-navigation-event-checker 架构说明

版本：AutoWSGR-3.0 第 1 版
状态：生效
适用范围：`autowsgr/application/ui/navigation/page_checker/event`
实现基线：`codex/20260913-shiinaskuya-upgrade-7b3e`，2026-10-10（本期推图活动 20260930）

## 1. 模块定位

event checker 是 **application 层导航器**的活动识别模块。它只负责把画面读成活动页面事实：
首页活动入口是否可见、活动地图当前难度、节点浮窗是否指向目标章节。

它明确不负责：点击操作（属于 UI 控制器）、路由计算与页面切换编排（属于导航器 service）、
识别失败后的报错与恢复（由拥有恢复策略的导航器决定）。

模块的状态与资源所有权：

- 识别事实由调用方传入的 `ContextHandle` 持有（截图事实），模块自身无状态；
- 模板与活动数据由 `calibration` 加载，模块不持有缓存；
- 坐标与模板路径由 `constants` 持有，每期活动只改这一份；
- 错误只使用入参校验的 `ValueError`，识别不产生业务错误。

## 2. 模块架构

### 2.1 目录树

```text
autowsgr/application/ui/navigation/page_checker/event_checker/
├── __init__.py            # 导出各活动 checker 模块
├── calibration.py         # 公共加载：模板（common.vision）与活动数据（common.system）
└── stage_push/        # 普通推图活动
    ├── __init__.py        # 模块入口：导出三个识别入口与事实模型
    ├── checker.py         # 页面事实模型 EventMapState + 三个识别入口
    ├── recognition.py     # 难度事实 EventMode + 识别读取与文本解析
    └── constants.py       # 活动标识、期号、识别坐标与模板路径
```

### 2.2 文件职责

| 文件/目录 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| `__init__.py` | 导出各活动 checker 模块 | 业务实现 |
| `calibration.py` | 加载活动模板、读取活动静态数据、校验活动玩法标识 | 解释业务含义、识别画面 |
| `stage_push/__init__.py` | 导出三个入口与两个事实模型 | 业务实现 |
| `stage_push/checker.py` | 入口编排、难度结论组装、页面事实模型 | 识别细节、读文件、点击 |
| `stage_push/recognition.py` | 调 `common.vision` 读取画面事实、解析识别文本 | 读文件、组装页面结论、点击 |
| `stage_push/constants.py` | 活动标识、期号、ROI、模板文件名 | 识别阈值、判定规则、运行时状态 |

### 2.3 依赖方向

```text
导航器 / 上层调用者
        ↓
event_checker.stage_push（模块入口）
        ↓
normal.checker
   ├──→ normal.recognition ──→ constants
   │                                   └──→ common.vision
   └──→ calibration ──→ common.system（读活动数据）
                     └──→ common.vision（读模板）
```

禁止方向：

- checker 不执行点击，不计算路由，不向处理器上报业务错误；
- recognition 不读取文件、不持有缓存；活动数据由 checker 传入；
- calibration 不解释业务语义，不认识难度、章节或页面；
- 本模块不反向依赖 UI 控制器，也不依赖 dispatch 之外的运行时服务。

### 2.4 公开出口策略

稳定出口只有模块入口 `event_checker.stage_push` 导出的对象：三个识别入口和两个事实模型。
`calibration` 只对同包内的 checker 可见；`stage_push` 的私有函数、`constants` 的具体常量
不得作为跨模块契约。

## 3. 能力总览

| 能力 | 对外入口 | 所在文件 | 输入 | 输出/副作用 | 负责内容 | 不负责内容 |
| --- | --- | --- | --- | --- | --- | --- |
| 首页活动入口识别 | `event_checker.stage_push.check_event_entry` | `stage_push/checker.py` | `ctx`、`event_type` | `bool`；不修改外部状态 | 判断入口卡片是否可见 | 点击入口、判断当前页面 |
| 活动地图状态读取 | `event_checker.stage_push.read_event_map_state` | `stage_push/checker.py` | `ctx`、`event_type` | `EventMapState`；不修改外部状态 | 读出难度事实与当前难度 | 切难度、判断是否该切 |
| 出征准备前置页确认 | `event_checker.stage_push.check_event_sortie_prepare` | `stage_push/checker.py` | `ctx`、`event_type`、`stage` | `bool`；不修改外部状态 | 确认节点浮窗指向目标章节 | 点章节、点出击准备 |
| 确认出征按钮中心读取 | `event_checker.stage_push.read_sortie_prepare_center` | `stage_push/checker.py` | `ctx`、`event_type` | 归一化中心或 `None` | 给出"确认出征"按钮中心 | 点击、判断浮窗状态 |
| 章节标识解析 | `event_checker.stage_push.parse_stage` | `stage_push/checker.py` | 章节标识 | `EventStage`；纯函数 | 给出难度与落点序号 | 点击、切难度 |
| 活动模板加载 | `event.calibration.load_activity_template` | `calibration.py` | 活动标识、文件名、名称 | `Template`；读模板文件 | 按活动目录加载模板 | 识别、缓存策略 |
| 活动数据加载 | `event.calibration.load_activity_data` | `calibration.py` | 活动标识、期号 | 数据映射；读数据文件 | 读取并缓存本期数据 | 解释数据语义 |

## 4. 首页活动入口识别

### 4.1 能力说明

用首页活动入口卡片的模板在固定区域内匹配，判断当前首页是否存在活动入口。它是活动链路的
前置条件：入口不可见时，上层不能继续进入活动地图。

### 4.2 稳定入口

```text
event_checker.stage_push.check_event_entry(ctx, *, event_type: str) -> bool
```

- `ctx`：提供设备服务与截图事实的 `ContextHandle`；
- `event_type`：活动玩法标识；与当前 checker 不一致时抛 `ValueError`；
- 返回：入口模板命中为 `True`；读不到为 `False`；
- 副作用：按 `common.vision` 的约定登记最新截图，不修改页面状态。

### 4.3 调用示例

```python
from autowsgr.application.ui.navigation.page_checker.event_checker import normal

visible = normal.check_event_entry(ctx, event_type='stage_push')
if not visible:
    # 上层决定：报错、重试或换路径
```

### 4.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 活动玩法标识不匹配 | 拒绝调用 | `ValueError` | 调用方 |
| 入口模板未命中 | 返回识别事实 | `False` | 导航器（决定报错或换路径） |
| 设备或 Context 异常 | 继续向上抛出 | 设备/Context 异常 | 导航器 |

### 4.5 维护规则

换期只改 `constants.HOME_ENTRY_ROI` 与新模板文件；判断逻辑不随活动期变化。
新增活动玩法时新建同级子包，不在此处加分支。

## 5. 活动地图状态读取

### 5.1 能力说明

一次调用读出两个独立证据并给出结论：左下角模式按钮显示的模式（按钮文字表示"要切换到的"
模式）与地图标题难度。节点浮窗打开时模式按钮模板失效，因此浮窗态不下难度结论。

### 5.2 稳定入口

```text
event_checker.stage_push.read_event_map_state(ctx, *, event_type: str) -> EventMapState
```

`EventMapState` 字段：

| 字段 | 含义 |
| --- | --- |
| `on_clean_map` | 是否为没有节点浮窗的干净地图页；为 `False` 时难度结论不可信 |
| `button_mode` | 模式按钮显示的模式（= 要切换到的难度）；无按钮时为 `None` |
| `title_mode` | 地图标题对应的难度；读不到时为 `None` |
| `current_mode` | 综合结论；浮窗态、证据矛盾或读不到时为 `None` |

结论规则：按钮显示普通 + 标题困难 ⇒ 当前困难；按钮显示困难 + 标题普通 ⇒ 当前普通；
无按钮 + 标题普通 ⇒ 当前普通（困难未开放）。

### 5.3 调用示例

```python
state = normal.read_event_map_state(ctx, event_type='stage_push')
if state.on_clean_map and state.current_mode is normal.EventMode.HARD:
    # 上层决定是否切换难度
```

### 5.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 活动玩法标识不匹配 | 拒绝调用 | `ValueError` | 调用方 |
| 浮窗已打开 | 只给事实 | `on_clean_map=False`、`current_mode=None` | 导航器先关浮窗 |
| 按钮与标题矛盾 | 只给事实 | `current_mode=None` | 导航器决定重试或报错 |
| 数据文件缺失或格式错误 | 拒绝读取 | `FileNotFoundError` / `KeyError` | 交付期发现，不允许运行时兜底 |

### 5.5 维护规则

新增难度或改变判定规则时改 `recognition`：阈值与文本规则在 `recognition`，坐标在 `constants`，
结论组合在 `checker`。难度判定必须保持在干净地图页。

## 6. 出征准备前置页确认

### 6.1 能力说明

点完章节后地图上出现节点浮窗，浮窗内有关卡标题和"出击准备"按钮。本能力确认浮窗已出现
且标题指向目标章节。

### 6.2 稳定入口

```text
event_checker.stage_push.check_event_sortie_prepare(ctx, *, event_type: str, stage: str) -> bool
event_checker.stage_push.read_sortie_prepare_center(ctx, *, event_type: str) -> tuple[float, float] | None
```

- `stage`：目标章节标识，例如 `EX7`；本期数据里没有该章节时抛 `ValueError`（入口第一行校验）；
- 判定：浮窗模板命中，且标题命中目标章节编号或章节名称（任一即可）。

### 6.3 调用示例

```python
if normal.check_event_sortie_prepare(ctx, event_type='stage_push', stage='EX7'):
    # 上层继续点出击准备
```

### 6.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 章节不在本期数据 | 拒绝调用 | `ValueError` | 调用方 |
| 浮窗未出现 | 返回识别事实 | `False` | 导航器 |
| 标题指向其它章节 | 返回识别事实 | `False` | 导航器 |

### 6.5 维护规则

章节名称与地图名是每期数据，放 `resources/data/map/event/<期>/<活动>.yaml`；标题解析规则
（忽略装饰字符、大小写不敏感、编号或名称任一命中）只在 `recognition` 内维护。

## 7. 章节标识解析

### 7.1 能力说明

把任务里的章节标识解析成执行参数：难度与地图落点序号。解析由**业务层执行器的上下文预处理**
完成一次，导航器与控制器只接收算好的值，不再解析字符串。

### 7.2 稳定入口

```text
event_checker.stage_push.parse_stage(stage: str) -> EventStage
```

`EventStage` 字段：

| 字段 | 含义 |
| --- | --- |
| `difficulty` | 章节难度（`EventMode.NORMAL` / `EventMode.HARD`） |
| `node` | 地图落点序号（1–6），普通与困难共用同一组落点 |

接受的写法：`EX1`–`EX12`（任务契约）、`E1`–`E6`（普通）、`H1`–`H6`（困难，等同 `EX7`–`EX12`）。

### 7.3 调用示例

```python
from autowsgr.application.ui.navigation.page_checker.event_checker import normal

stage = normal.parse_stage(ctx.read_event_stage())
# 导航器据此决定是否切换难度；控制器用 stage.node 点击章节入口
```

### 7.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 标识格式非法或超出范围 | 拒绝解析 | `ValueError` | 业务层执行器 |
| 合法标识 | 返回执行参数 | `EventStage` | 业务层执行器 |

### 7.5 维护规则

新增或调整章节编号规则时改 `_stage_number` 与落点数量；落点表在 UI 控制器的
`event_page/stage_push/constants.py`，两边的落点数量必须一致。

## 8. 统一配置

本模块无运行时配置。

活动标识与期号是代码常量（`stage_push/constants.py`），因为换期必须同时换模板与数据文件；
把它们做成用户配置只会让资源和代码版本脱节。

## 9. 错误约定

模块不定义错误类型，也不上报识别错误：

| 场景 | 行为 | 异常 | 处理者 |
| --- | --- | --- | --- |
| 入参非法（玩法标识、章节） | 拒绝调用 | `ValueError` | 调用方 |
| 活动数据文件缺失或结构错误 | 拒绝读取 | `FileNotFoundError` / `KeyError` | 交付期修正 |
| 识别不到目标 | 返回事实 | 无 | 导航器决定报错、重试或换路 |

`common.vision` 的重试耗尽只返回 `satisfied=False`；"读不到就报错"属于拥有恢复策略的
导航器，本模块不替它决定。

## 10. 日志约定

- 日志对象：`autowsgr.common.system.logger.get_logger`，channel 为 `ui`；
- 级别：全部使用 `DEBUG`，因为本模块只产生识别事实，没有页面动作；
- 格式：`[UI] 位置 → 动作：名=值`，使用 loguru 占位符 `{}` / `{!r}`。

| 位置 | 记录内容 |
| --- | --- |
| `活动数据` | 加载的活动标识与期号 |
| `活动识别` | 读模式按钮、读地图标题、读关卡标题、判节点浮窗、查活动入口的结果 |
| `活动地图` | 页面状态结论（干净页、按钮模式、标题模式、当前难度） |
| `出征准备前置页` | 目标章节与标题是否命中 |

不记录原始截图、完整 OCR 长文本或设备信息；不重复记录 `common.vision` 已输出的匹配分数。

## 11. 公开出口和调用边界

### 10.1 稳定出口

| 出口 | 来源 | 调用者可以做什么 | 调用者不能做什么 |
| --- | --- | --- | --- |
| `event_checker.stage_push.check_event_entry` | `stage_push/checker.py` | 判断首页活动入口是否可见 | 用它代替点击入口 |
| `event_checker.stage_push.read_event_map_state` | `stage_push/checker.py` | 读取地图难度事实与结论 | 用它决定切难度后再点击 |
| `event_checker.stage_push.check_event_sortie_prepare` | `stage_push/checker.py` | 确认浮窗指向目标章节 | 用它点出击准备 |
| `event_checker.stage_push.EventMode` | `stage_push/recognition.py` | 比较难度结论 | 当作页面状态写入上下文 |
| `event_checker.stage_push.EventMapState` | `stage_push/checker.py` | 读取页面事实 | 修改其字段（模型不可变） |
| `event_checker.stage_push.parse_stage` | `stage_push/checker.py` | 把章节标识解析成执行参数 | 在控制器或导航器里重复解析 |
| `event_checker.stage_push.EventStage` | `stage_push/checker.py` | 读取难度与落点序号 | 修改其字段（模型不可变） |

### 10.2 内部内容

`calibration` 的加载函数只服务同包 checker；`stage_push` 的私有解析函数（标题归一化、
编号解析、难度结论组合）以及 `constants` 的具体常量都是实现细节。测试直接调用私有函数
不使其成为生产出口。

## 12. 模块维护方法

### 12.1 业务层执行器的上下文预处理

任务参数的解析（如章节标识 → 难度与落点）属于**业务层执行器**：它在启动时调用 `parse_stage`
一次，把结果沿调用链传给导航器与控制器。dispatch 只把任务原始值存进上下文，控制器只接收
算好的落点序号，任何一层都不在点击前临时解析字符串。

### 12.2 换期（每期活动都做）

1. 把新模板放进 `resources/image/application/ui/navigation/page_checker/event_checker/stage_push/`；
2. 新增 `resources/data/map/event/<期>/normal.yaml`（地图名 + 关卡名称）；
3. 改 `constants.PERIOD`；ROI 变化时同步改 `constants` 的 ROI；
4. 用静态帧 case 跑一遍外挂截图，确认三个入口行为不变。

### 12.3 新增活动玩法（命名约定）

玩法子包用**语义化的完整名称**，不用泛称：`stage_push`（推图）、立体强袭、舰队问答等各自一个同级子包。
历史上"推图"曾叫 `normal`，与难度 `EventMode.NORMAL` 撞名，已改为 `stage_push`；新增玩法时先确认
名字不会与难度、页面名或任务类型重名。

### 12.4 新增活动玩法

新建同级子包（如 `assault_checker/`），复制 `stage_push` 的结构再改；父包
`event/__init__.py` 增加导出。玩法之间允许重复，不提前抽公共基类。

### 12.5 新增识别能力

先在 `recognition` 增加读取与解析，阈值留在 `recognition`；需要新常量时加在 `constants`
（只放坐标与模板路径）；再由 `checker` 组装并在模块入口导出。

### 12.6 修改公开契约

同步更新本文件的能力总览、对应能力章节、公开出口表，并更新实现基线。

## 13. 验收门禁

| 检查 | 现状 |
| --- | --- |
| 模块入口 import smoke | 通过 |
| 模块专属 pytest（`testing/ui/page_checker/test_event_page.py`） | 12 项通过 |
| 入参校验（玩法标识、章节越界） | 覆盖 |
| 事实表 7 种场景（含浮窗态、矛盾、读不到） | 覆盖 |
| 标题编号与名称两条判定分支 | 覆盖 |
| 真图静态验证（`e2e --static event_check`） | 8 步通过 |
| 日志级别与格式 | 已按 §9 落地 |
| 未验证项 | 实机点击链路（依赖导航器编排与完整 E2E 模式，未实现） |

## 14. TODO：后续活动玩法（未实现）

按 §12.3 的命名约定，后续玩法各自一个同级子包，结构与 `stage_push` 相同：

| 玩法 | 建议标识 | checker 包 | 模板目录 | 数据文件 | 任务值 |
| --- | --- | --- | --- | --- | --- |
| 立体强袭 | `dimensional_assault` | `event_checker/dimensional_assault/` | `page_checker/event_checker/dimensional_assault/` | `resources/data/map/event/<期>/dimensional_assault.yaml` | `event: dimensional_assault` |
| 舰队问答 | `fleet_quiz` | `event_checker/fleet_quiz/` | 同上 | 同上 | `event: fleet_quiz` |

每个新玩法子包至少包含四个文件（与 `stage_push` 同构）：

| 文件 | 负责内容 |
| --- | --- |
| `__init__.py` | 导出识别入口与事实模型 |
| `checker.py` | 入口编排 + 事实模型（放文件顶部） |
| `recognition.py` | 模板匹配与解析；阈值放这里，垂直调用 `common.vision` |
| `constants.py` | `TEMPLATE_NAMESPACE`、模板文件名（目录小写、文件名全大写）、识别区域（四位小数） |

约定：

1. **标识用语义化完整名称**，不用泛称（`normal` 撞难度的教训）；
2. 舰队问答需要 OCR 识别题目与选项，识别入口仍放 `recognition.py`，**不在控制器里识别**；
3. 章节/关卡参数的解析入口（如 `parse_stage`）放各自子包的 `checker.py`，由业务层执行器调用一次；
4. 两个新玩法的标识待用户最终确认后写进本文件与 event page 的对应文档。
