# application-ui-controller-home-event-page 架构说明

版本：AutoWSGR-3.0 第 1 版
状态：生效
适用范围：`autowsgr/application/ui/controller/home/event_page`
实现基线：`codex/20260913-shiinaskuya-upgrade-7b3e`，2026-10-10

## 1. 模块定位

event page 是 **application 层 UI 控制器**的活动页面单击控制器。它只负责一件事：把"点哪里"
变成一次点击。

它明确不负责：画面识别（属于 `event_checker`）、等待与确认（属于导航器）、流程编排（属于
业务层执行器与导航器）、任务参数解析（属于业务层执行器的上下文预处理）。

模块的所有权：

- 点击落点由本模块的 `constants` 持有（固定坐标）或由调用方传入（识别产出的中心）；
- 点击能力来自 `common.device.service`，通过 `ctx.runtime.ctrl` 垂直调用；
- 模块自身无状态、不缓存、不识别、不等待。

## 2. 模块架构

### 2.1 目录树

```text
autowsgr/application/ui/controller/home/event_page/
├── __init__.py            # 模块入口：导出 EventPage
├── page.py                # EventPage：五个公开入口，只做单次点击
├── constants.py           # 跨玩法通用落点（返回首页、关闭浮窗）
└── stage_push/            # 推图玩法，只放本玩法坐标
    ├── __init__.py        # 导出坐标命名空间
    └── constants.py       # 章节落点、确认出征兜底
```

### 2.2 文件职责

| 文件/目录 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| `__init__.py` | 导出 `EventPage` | 业务实现 |
| `page.py` | 五个单击入口、玩法落点表登记 | 识别、等待、解析、重试 |
| `constants.py` | 跨玩法通用落点 | 玩法特有坐标、识别区域 |
| `stage_push/constants.py` | 推图玩法的章节落点与兜底落点 | 页面动作、识别规则 |

### 2.3 依赖方向

```text
导航器 / 业务层执行器
        ↓
event_page.EventPage
        ├──→ event_page.constants（通用落点）
        ├──→ event_page.stage_push.constants（玩法落点）
        └──→ common.device.service（经 ctx.runtime.ctrl 点击）
```

禁止方向：

- 不 import `event_checker`（识别归导航器，控制器不反向依赖）；
- 不等待页面、不重试、不判断结果；
- 不在控制器里解析任务字符串（如 `EX7` → 落点）；
- 玩法子包不放页面动作，页面动作统一在 `page.py`。

### 2.4 公开出口策略

稳定出口只有模块入口导出的 `EventPage` 及其五个公开方法。两个 `constants` 只服务本模块，
不作为跨模块契约。

## 3. 能力总览

| 能力 | 对外入口 | 输入 | 输出/副作用 | 负责内容 | 不负责内容 |
| --- | --- | --- | --- | --- | --- |
| 进入章节浮窗 | `EventPage.go_to_overlay` | 落点序号 | 一次点击 | 查表并点击章节入口 | 确认浮窗是否出现 |
| 进入编队页 | `EventPage.go_to_prepare` | 识别中心 | 一次点击 | 点击"确认出征" | 确认是否到达编队页 |
| 切换难度 | `EventPage.switch_difficulty` | 识别中心 | 一次点击 | 点击难度按钮 | 判断当前难度、决定是否切换 |
| 关闭章节浮窗 | `EventPage.click_overlay_close` | 无 | 一次点击 | 点击浮窗关闭按钮 | 确认浮窗已关闭 |
| 返回首页 | `EventPage.go_back` | 无 | 一次点击 | 点击返回按钮 | 确认已回到首页 |

## 4. 进入章节浮窗

### 4.1 能力说明

章节入口在地图上的位置固定（普通 EX1–EX6 与困难 EX7–EX12 共用同一组六个落点），因此控制器
只接收**落点序号**，不接收章节字符串。

### 4.2 稳定入口

```text
EventPage.go_to_overlay(node: int) -> None
```

- `node`：落点序号（1–6），由业务层执行器的上下文预处理给出；
- 副作用：一次点击；不修改上下文、不等待页面。

### 4.3 调用示例

```python
from autowsgr.application.ui.controller.home.event_page import EventPage

page = EventPage(ctx, event_type='stage_push')
stage = normal.parse_stage(ctx.read_event_stage())   # 业务层执行器已做上下文预处理
page.go_to_overlay(stage.node)
```

### 4.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 落点序号不在落点表 | 拒绝点击 | `ValueError` | 业务层执行器 |
| 活动玩法没有落点表 | 拒绝点击 | `ValueError` | 业务层执行器 |
| 正常落点 | 点击一次 | 无 | 导航器负责确认 |

### 4.5 维护规则

换期若章节落点变化，只改 `stage_push/constants.py`；落点数量必须与
`event_checker.stage_push.parse_stage` 的落点数保持一致。

## 5. 进入编队页

### 5.1 能力说明

"确认出征"按钮位于章节浮窗内，浮窗位置随节点变化，因此落点必须由 checker 识别产出后传入；
没有识别中心说明按钮位置不可信，调用方不得点击。

### 5.2 稳定入口

```text
EventPage.go_to_prepare(position: tuple[float, float]) -> None
```

### 5.3 调用示例

```python
center = normal.read_sortie_prepare_center(ctx, event_type='stage_push')   # checker 给出中心
if center is not None:
    page.go_to_prepare(center)
```

### 5.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 传入识别中心 | 按中心点击 | 无 | 导航器 |
| 未传中心 | 使用兜底落点 | 无 | 导航器 |

### 5.5 维护规则

兜底落点只保证"点得下去"，不保证点得准；识别能力补齐后应优先传中心。

## 6. 切换难度

### 6.1 能力说明

难度按钮每期活动位置可能变化，落点必须来自模板匹配产出的中心（`TemplateMatchResult.center`）。

### 6.2 稳定入口

```text
EventPage.switch_difficulty(position: tuple[float, float]) -> None
```

### 6.3 调用示例

```python
button = normal.read_mode_button(ctx)
page.switch_difficulty(button.center)
```

### 6.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 传入识别中心 | 点击一次 | 无 | 导航器 |
| 识别未命中（中心为空） | 调用方不应调用 | 无 | 导航器 |

### 6.5 维护规则

难度按钮模板每期维护，模板按按钮本体裁切，因此匹配中心即按钮中心。

## 7. 关闭章节浮窗与返回首页

### 7.1 能力说明

两个后退动作，落点固定，不需要识别：

- `click_overlay_close`：章节浮窗 → 活动地图；
- `go_back`：活动地图 → 首页。

### 7.2 稳定入口

```text
EventPage.click_overlay_close() -> None
EventPage.go_back() -> None
```

### 7.3 调用示例

```python
page.click_overlay_close()   # 回到活动地图
page.go_back()               # 回到首页
```

### 7.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 调用任一个 | 点击一次 | 无 | 导航器负责确认目标页 |

### 7.5 维护规则

坐标来自用户标注截图（1280x720 归一化、四位小数）；游戏 UI 大改后需重新标注。

## 8. 统一配置

本模块无运行时配置。玩法标识由构造参数给出，落点是代码常量。

## 9. 错误约定

模块不定义错误类型：

| 场景 | 行为 | 异常 | 处理者 |
| --- | --- | --- | --- |
| 落点序号或玩法不受支持 | 拒绝点击 | `ValueError` | 业务层执行器 |
| 点击本身失败 | 继续向上抛出 | 设备异常 | 导航器 |

## 10. 日志约定

- 日志对象：`autowsgr.common.system.logger.get_logger`，channel 为 `ui.home.event_page`；
- 级别：全部 `INFO`（每次都是一次真实页面动作）；
- 格式：`[UI] 活动页面 → 动作：名={!r}`。

| 位置 | 记录内容 |
| --- | --- |
| `活动页面` | 点击章节入口（含落点）、确认出征、难度按钮、关闭浮窗、返回首页 |

不记录截图、设备信息和识别分数。

## 11. 公开出口和调用边界

### 11.1 稳定出口

| 出口 | 调用者可以做什么 | 调用者不能做什么 |
| --- | --- | --- |
| `EventPage` | 构造一次点击控制器 | 在控制器里做识别或等待 |
| `EventPage.go_to_overlay` | 点章节入口 | 传章节字符串（只收落点序号） |
| `EventPage.go_to_prepare` | 点确认出征 | 期望它确认页面已切换 |
| `EventPage.switch_difficulty` | 点难度按钮 | 期望它判断当前难度 |
| `EventPage.click_overlay_close` | 关浮窗 | 期望它确认浮窗已关闭 |
| `EventPage.go_back` | 回首页 | 期望它确认已到首页 |

### 11.2 内部内容

两个 `constants` 的坐标、玩法落点映射表都是实现细节，不作为跨模块契约。

## 12. 模块维护方法

### 12.1 业务层执行器的上下文预处理

控制器只接收**算好的落点序号**；章节标识的解析由业务层执行器调用
`event_checker.stage_push.parse_stage` 完成一次。

### 12.2 换期（每期活动都做）

1. 章节落点变化时改 `stage_push/constants.py`；
2. 返回与关浮窗坐标若随 UI 变化，重新标注后按四位小数更新 `constants.py`；
3. 难度与确认出征不需要改坐标（来自识别中心）。

### 12.3 新增玩法

按 §13 的约定新增同级子包，并在玩法落点表里登记。

### 12.4 修改公开契约

同步更新能力总览、对应能力章节、公开出口表和实现基线。

## 13. TODO：后续活动玩法（未实现）

控制器按玩法分子包，子包**只放本玩法的点击坐标**，页面动作统一留在 `page.py`：

| 玩法 | 建议标识 | 控制器子包 | 任务值 |
| --- | --- | --- | --- |
| 立体强袭 | `dimensional_assault` | `event_page/dimensional_assault/constants.py` | `event: dimensional_assault` |
| 舰队问答 | `fleet_quiz` | `event_page/fleet_quiz/constants.py` | `event: fleet_quiz` |

新增玩法时：

1. 在玩法落点映射表里登记该玩法（没有落点表就登记空表或专用结构）；
2. **只有玩法确实需要不同的页面动作**时才新增方法，不为"以后可能需要"预留；
3. 落点来自识别中心的按钮继续由调用方传坐标，控制器不自己识别；
4. 两个新玩法的标识待用户最终确认后写进本文件与 `event_checker` 的对应文档。

## 14. 验收门禁

| 检查 | 现状 |
| --- | --- |
| 模块入口 import smoke | 通过 |
| 模块专属 pytest（`testing/ui/controller/test_event_page.py`） | 10 项通过 |
| 落点序号合法与非法路径 | 覆盖 |
| 识别中心优先与兜底落点 | 覆盖 |
| 固定落点（关浮窗、返回首页） | 覆盖 |
| 未支持玩法 | 覆盖 |
| 未验证项 | 实机点击链路（依赖导航器编排，未实现） |
