# application-ui-controller-home-main-page 架构说明

版本：AutoWSGR-3.0 第 1 版
状态：生效
适用范围：`autowsgr/application/ui/controller/home/main_page`
实现基线：`codex/20260913-shiinaskuya-upgrade-7b3e`，2026-10-10

## 1. 模块定位

home main page 是 **application 层 UI 控制器**的主页单击控制器。它只负责把"点哪里"变成一次点击，
并保留主页自己使用的通知红点识别。

它明确不负责：主页画面识别（属于 `home_checker`）、浮窗处理流程与页面确认（属于导航器）、
任务参数处理（属于业务层执行器）。

模块的所有权：

- 点击落点由本模块的 `constants` 持有（导航落点、公告关闭落点），或由调用方传入（识别中心）；
- 点击能力来自 `common.device.service`，通过 `ctx.runtime.ctrl` 垂直调用；
- 通知红点识别与探针数据留在本模块（主页自己用的状态判断）；
- 模块不缓存、不等待、不重试。

## 2. 模块架构

### 2.1 目录树

```text
autowsgr/application/ui/controller/home/main_page/
├── __init__.py        # 模块入口：导出 HomePage、Target 与通知识别
├── page.py            # HomePage：五个单击入口 + Target 导航目标
├── constants.py       # 导航落点、浮窗点击落点、通知探针
└── recognition.py     # 主页通知红点识别（保留在控制器）
```

### 2.2 文件职责

| 文件 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| `__init__.py` | 导出稳定入口 | 业务实现 |
| `page.py` | 五个单击入口、导航目标枚举 | 识别、等待、流程编排 |
| `constants.py` | 静态落点与通知探针 | 识别规则、流程参数 |
| `recognition.py` | 通知红点颜色判定 | 页面识别、点击 |

### 2.3 依赖方向

```text
导航器 / 业务层执行器
        ↓
main_page.HomePage
        ├──→ main_page.constants（落点与探针）
        └──→ common.device.service（经 ctx.runtime.ctrl 点击）
```

禁止方向：

- 不 import `home_checker`（识别归导航器）；
- 不等待页面、不重试、不编排浮窗流程；
- 不在控制器里做主页页面识别（通知识别除外，它是控制器自用的状态判断）。

### 2.4 公开出口策略

稳定出口是 `HomePage`、`Target` 与两个通知识别函数；`constants` 只服务本模块。

## 3. 能力总览

| 能力 | 对外入口 | 输入 | 输出/副作用 | 负责内容 | 不负责内容 |
| --- | --- | --- | --- | --- | --- |
| 进入目标页 | `HomePage.go_to` | `Target` | 一次点击 | 查表并点击目标页入口 | 确认是否到达目标页 |
| 勾选公告 | `HomePage.click_news_checkbox` | 识别中心或固定落点 | 一次点击 | 点击勾选框 | 判断勾选状态 |
| 关闭公告 | `HomePage.click_news_close` | 无 | 一次点击 | 点击公告关闭按钮 | 确认公告已关闭 |
| 领取每日奖励 | `HomePage.click_reward_claim` | 识别中心或固定落点 | 一次点击 | 点击领取按钮 | 确认浮窗已切换 |
| 确认奖励 | `HomePage.click_reward_confirm` | 识别中心或固定落点 | 一次点击 | 点击确认按钮 | 确认浮窗已关闭 |
| 通知识别 | `check_expedition_ready` / `check_task_ready` | 截图 | `bool` | 判定通知红点是否出现 | 点击、页面跳转 |

## 4. 进入目标页

### 4.1 能力说明

主页五个入口位置固定（出征、任务、侧边栏、后院、活动），因此控制器只用 `NAV_POSITIONS` 查表，
不接收外部坐标。

### 4.2 稳定入口

```text
HomePage.go_to(target: Target) -> None
```

`Target` 与页面名的对应由 `_TARGET_PAGES` 维护，供导航器读取目标页。

### 4.3 调用示例

```python
from autowsgr.application.ui.controller.home.main_page import HomePage, Target

page = HomePage(ctx)
page.go_to(Target.SORTIE)
```

### 4.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 目标没有落点 | 拒绝点击 | `ValueError` | 导航器 |
| 正常目标 | 点击一次 | 无 | 导航器负责确认 |

### 4.5 维护规则

主页入口位置变化时改 `constants.NAV_POSITIONS`；新增目标页时同时补 `Target` 与 `_TARGET_PAGES`。

## 5. 每日浮窗按钮

### 5.1 能力说明

四个浮窗按钮中，勾选框、领取、确认的落点随浮窗位置变化，由 checker 识别产出后传入；
识别不到中心时退回 `OVERLAY_POSITIONS` 的固定落点，保证模板匹配失败仍能点击。公告关闭按钮
没有模板，位置固定，直接用 `OVERLAY_POSITIONS`。

### 5.2 稳定入口

```text
HomePage.click_news_checkbox(position: tuple[float, float] | None = None) -> None
HomePage.click_news_close() -> None
HomePage.click_reward_claim(position: tuple[float, float] | None = None) -> None
HomePage.click_reward_confirm(position: tuple[float, float] | None = None) -> None
```

### 5.3 调用示例

```python
state = home_checker.check_home_news_overlay(ctx)
if state.matched and state.checked is False:
    page.click_news_checkbox(checkbox_center)
```

### 5.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 传入识别中心 | 按中心点击 | 无 | 导航器 |
| 未传中心（勾选/领取/确认） | 调用方不应调用 | 无 | 导航器 |

### 5.5 维护规则

浮窗按钮位置由识别产出，通常不需要改常量；公告关闭按钮变化时改 `OVERLAY_POSITIONS`。

## 6. 通知识别（保留在控制器）

### 6.1 能力说明

主页通知红点用于判断远征、任务是否完成，属控制器自用的状态判断，因此不迁入 checker。

### 6.2 稳定入口

```text
check_expedition_ready(ctx: ContextHandle) -> bool
check_task_ready(ctx: ContextHandle) -> bool
```

识别入口自己截图（通过 `ctx`），调用方不再传截图。

### 6.3 调用示例

```python
if check_task_ready(screen):
    page.go_to(Target.TASK)
```

### 6.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 采样位置命中红点 | 返回事实 | `True` | 业务层 |

### 6.5 维护规则

通知识别走 `common.vision.expect_pixels` 与 `constants` 里的像素签名（探针位置、通知红、容差），
`attempts=1` 表示单帧探测、不等待。通知位置或颜色变化时改签名即可，不要改识别函数。

## 7. 统一配置

本模块无运行时配置。

## 8. 错误约定

| 场景 | 行为 | 异常 | 处理者 |
| --- | --- | --- | --- |
| 目标没有落点 | 拒绝点击 | `ValueError` | 导航器 |
| 点击本身失败 | 继续向上抛出 | 设备异常 | 导航器 |

## 9. 日志约定

- 日志对象：`get_logger('ui.home.main_page')`；
- 级别：全部 `INFO`（每次都是一次真实页面动作）；
- 格式：`[UI] 主页面 → 动作：名={!r}`。

| 位置 | 记录内容 |
| --- | --- |
| `主页面` | 进入目标页、勾选公告、关闭公告、领取奖励、确认奖励 |

## 10. 公开出口和调用边界

### 10.1 稳定出口

| 出口 | 调用者可以做什么 | 调用者不能做什么 |
| --- | --- | --- |
| `HomePage` | 构造主页单击控制器 | 在控制器里做页面识别或等待 |
| `HomePage.go_to` | 点目标页入口 | 期望它确认已到达 |
| `HomePage.click_news_checkbox` | 点勾选框 | 期望它判断勾选状态 |
| `HomePage.click_news_close` | 关公告 | 期望它确认公告已关闭 |
| `HomePage.click_reward_claim` | 点领取 | 期望它确认浮窗切换 |
| `HomePage.click_reward_confirm` | 点确认 | 期望它确认浮窗关闭 |
| `Target` | 表达导航目标 | 在控制器外直接改页面映射 |
| `check_expedition_ready` / `check_task_ready` | 读取通知状态 | 传裸截图（入口只收 `ctx`） |

### 10.2 内部内容

`constants` 的落点与探针、`_TARGET_PAGES` 都是实现细节。

## 11. 模块维护方法

### 11.1 业务层执行器的上下文预处理

控制器只接收算好的落点或识别中心；主页不涉及章节解析。

### 11.2 浮窗流程与页面确认归导航器

浮窗处理（识别 → 点击 → 再识别）与页面到达确认由导航器用 `expect_*` 编排；本批已删除
`dismiss_current_overlay` 与旧 `workflow.py`。

### 11.3 修改公开契约

同步更新能力总览、对应能力章节、公开出口表和实现基线。

## 12. TODO：后续活动玩法（未实现）

活动页面的控制器约定与主页无关，但两者共用同一套控制器形状，新玩法开工时按此办理：

| 玩法 | 建议标识 | 控制器子包 | 任务值 |
| --- | --- | --- | --- |
| 立体强袭 | `dimensional_assault` | `event_page/dimensional_assault/constants.py` | `event: dimensional_assault` |
| 舰队问答 | `fleet_quiz` | `event_page/fleet_quiz/constants.py` | `event: fleet_quiz` |

主页自身暂不需要按玩法拆分。

## 13. 验收门禁

| 检查 | 现状 |
| --- | --- |
| 模块入口 import smoke | 通过 |
| 模块专属 pytest（`testing/ui/controller/test_home_page.py`） | 6 项通过（控制器目录合计 21 passed） |
| 五个导航目标落点 | 覆盖 |
| 缺落点的目标 | 覆盖 |
| 识别中心与固定落点两条路径 | 覆盖 |
| 通知识别（像素签名 + `expect_pixels`） | 已升级，单测覆盖签名与单帧探测 |
| 未验证项 | 实机点击链路（依赖导航器编排） |
| 用户验收 | 通过（2026-10-10） |
