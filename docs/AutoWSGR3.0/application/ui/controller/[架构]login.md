# application-ui-controller-login 架构说明

版本：AutoWSGR-3.0 第 1 版
状态：生效
适用范围：`autowsgr/application/ui/controller/login`
实现基线：`codex/20260913-shiinaskuya-upgrade-7b3e`，2026-10-11

## 1. 模块定位

login 是 **application 层 UI 控制器**的登录页单击控制器。它只负责把"点哪里"变成一次点击：
进入游戏、打开区服列表、选择区服。

它明确不负责：登录各画面的识别（属于 `login_checker`）、启动流程的分支与"需要更新"的报错
（属于 dispatch 处理器）、页面到达确认（属于导航器）。

模块的所有权：

- 点击落点由本模块的 `constants` 持有；登录页与换区入口的落点可被调用方传入的识别中心覆盖，
  区服条目只按序号查表；
- 点击能力来自 `common.device.service`，通过 `ctx.runtime.ctrl` 垂直调用；
- 模块不保存画面事实、不缓存、不等待、不重试。

## 2. 模块架构

### 2.1 目录树

```text
autowsgr/application/ui/controller/login/
├── __init__.py        # 模块入口：导出 LoginPage
├── page.py            # LoginPage：三个单击入口
└── constants.py       # 进入游戏、换区入口与四个区服条目的落点
```

本模块没有 `recognition.py`：登录画面的识别全部归 `login_checker`，控制器不读取画面。

### 2.2 文件职责

| 文件 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| `__init__.py` | 导出稳定入口 | 业务实现 |
| `page.py` | 进入游戏、打开区服列表、选择区服三个单击入口 | 识别、等待、流程编排 |
| `constants.py` | 登录页落点与四个区服条目落点 | 识别规则、流程参数 |

### 2.3 依赖方向

```text
导航器 / dispatch 启动流程
        ↓
login.LoginPage
        ├──→ login.constants（落点）
        └──→ common.device.service（经 ctx.runtime.ctrl 点击）
```

禁止方向：

- 不 import `login_checker`（识别归导航器）；
- 不判断是否需要更新、不抛启动阶段错误；
- 不等待页面、不重试、不编排登录流程。

### 2.4 公开出口策略

稳定出口只有模块入口导出的 `LoginPage`；`constants` 只服务本模块，不作为跨模块契约。

## 3. 能力总览

| 能力 | 对外入口 | 输入 | 输出/副作用 | 负责内容 | 不负责内容 |
| --- | --- | --- | --- | --- | --- |
| 进入游戏 | `LoginPage.click_enter_game` | 识别中心或空 | 一次点击 | 点击"进入游戏"按钮 | 确认是否进入主页 |
| 打开区服列表 | `LoginPage.click_switch_entry` | 识别中心或空 | 一次点击 | 点击"点击换区"入口 | 确认列表是否出现 |
| 选择区服 | `LoginPage.click_server` | 区服序号 | 一次点击 | 按序号查表点击区服条目 | 判断是否切换成功 |

## 4. 进入游戏

### 4.1 能力说明

"进入游戏"按钮位于登录页固定位置，落点由 `CLICK_ENTER_GAME` 持有；调用方从 checker 拿到
识别中心时优先使用中心，拿不到时退回固定落点。

### 4.2 稳定入口

```text
LoginPage.click_enter_game(position: tuple[float, float] | None = None) -> None
```

### 4.3 调用示例

```python
from autowsgr.application.ui.controller.login import LoginPage
from autowsgr.application.ui.navigation.page_checker import login_checker

page = LoginPage(ctx)
page.click_enter_game(login_checker.read_enter_button_center(ctx))
```

### 4.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 传入识别中心 | 按中心点击 | 无 | 导航器 |
| 不传中心 | 按固定落点点击 | 无 | 导航器 |
| 点击本身失败 | 继续向上抛出 | 设备异常 | 启动流程处理器 |

### 4.5 维护规则

登录页按钮位置变化时改 `constants.CLICK_ENTER_GAME`；模板位置变化时同时改
`login_checker.constants.ENTER_BUTTON_ROI`，两者是同一按钮的两种表示。

## 5. 打开区服列表

### 5.1 能力说明

"点击换区"入口位置固定，落点由 `CLICK_SWITCH_ENTRY` 持有；与进入游戏同样支持识别中心优先、
固定落点兜底。点击后区服列表出现，是否出现由 `login_checker.check_server_select` 确认。

### 5.2 稳定入口

```text
LoginPage.click_switch_entry(position: tuple[float, float] | None = None) -> None
```

### 5.3 调用示例

```python
page.click_switch_entry(login_checker.read_switch_entry_center(ctx))
```

### 5.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 传入识别中心 | 按中心点击 | 无 | 导航器 |
| 不传中心 | 按固定落点点击 | 无 | 导航器 |

### 5.5 维护规则

换区入口位置变化时改 `constants.CLICK_SWITCH_ENTRY`；模板位置变化时同时改
`login_checker.constants.SWITCH_ENTRY_ROI`。

## 6. 选择区服

### 6.1 能力说明

区服列表固定不滚动，四个条目的位置写死在 `SERVER_POSITIONS`，控制器只按序号查表，不接收坐标。
序号与列表从上到下的顺序一致：0 胡德 / 1 俾斯麦 / 2 昆西 / 3 长春；名称本身由 `login_checker` 用
OCR 定位，控制器不读文字。

### 6.2 稳定入口

```text
LoginPage.click_server(position: int) -> None
```

### 6.3 调用示例

```python
index = login_checker.find_server_position(ctx, "昆西")
if index is not None:
    page.click_server(index)
```

### 6.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 序号超出区服范围 | 拒绝点击 | `ValueError` | 导航器 |
| 正常序号 | 点击一次 | 无 | 导航器负责确认回到登录页 |

### 6.5 维护规则

区服列表增删或顺序变化时改 `constants.SERVER_POSITIONS`，并同步
`login_checker.constants.SERVER_NAME_ROIS` 与 `SERVER_NAMES`。

## 7. 统一配置

本模块无运行时配置。

## 8. 错误约定

| 场景 | 行为 | 异常 | 处理者 |
| --- | --- | --- | --- |
| 区服序号越界 | 拒绝点击 | `ValueError` | 导航器 |
| 点击本身失败 | 继续向上抛出 | 设备异常 | 启动流程处理器 |

登录阶段的"需要更新"不是本模块的错误：`login_checker.check_update_prompt` 只返回事实，
由 dispatch 处理器决定报错与后续处置。

## 9. 日志约定

- 日志对象：`get_logger('ui.login')`；
- 级别：全部 `INFO`（每次都是一次真实页面动作）；
- 格式：`[UI] 登录页 → 动作：position={!r}`、`[UI] 区服列表 → 选择区服：position={}，target={!r}`。

| 位置 | 记录内容 |
| --- | --- |
| `登录页` | 进入游戏、打开区服列表 |
| `区服列表` | 选择区服（带序号与落点） |

## 10. 公开出口和调用边界

### 10.1 稳定出口

| 出口 | 调用者可以做什么 | 调用者不能做什么 |
| --- | --- | --- |
| `LoginPage` | 构造登录页单击控制器 | 在控制器里做画面识别或等待 |
| `LoginPage.click_enter_game` | 点进入游戏按钮 | 期望它确认已进入主页 |
| `LoginPage.click_switch_entry` | 打开区服列表 | 期望它确认列表已出现 |
| `LoginPage.click_server` | 按序号点区服条目 | 期望它判断换区是否成功 |

### 10.2 内部内容

`constants` 的三个落点都是实现细节。

## 11. 模块维护方法

### 11.1 识别归 login_checker

登录六个画面的识别、区服名 OCR 定位和模板中心读取全在 `login_checker`；控制器只接收算好的
中心或序号，不 import checker。

### 11.2 启动流程归 dispatch 处理器

"先后识别、再前识别"的启动分支、"需要更新"的报错、失败后的重启都由 dispatch 处理器编排；
控制器不参与判断。

### 11.3 修改公开契约

同步更新能力总览、对应能力章节、公开出口表和实现基线。

## 12. 验收门禁

| 检查 | 现状 |
| --- | --- |
| 模块入口 import smoke | 通过 |
| 模块专属 pytest（`testing/ui/controller/test_login_page.py`） | 8 项通过 |
| 三个入口的固定落点 | 覆盖 |
| 识别中心覆盖固定落点（进入游戏、打开区服列表） | 覆盖 |
| 区服序号越界 | 覆盖 |
| 未验证项 | 实机点击链路（依赖启动流程） |
| 用户验收 | 通过（2026-10-11） |
