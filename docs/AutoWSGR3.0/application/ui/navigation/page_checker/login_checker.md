# application-ui-navigation-login-checker 架构说明

版本：AutoWSGR-3.0 第 1 版
状态：生效
适用范围：`autowsgr/application/ui/navigation/page_checker/login_checker`
实现基线：`codex/20260913-shiinaskuya-upgrade-7b3e`，2026-10-11

## 1. 模块定位

login checker 是 **application 层导航器**的登录流程识别模块。它只负责把画面读成登录阶段的事实：
是否停在健康游戏提示、是否出现更新提示、是否正在加载、是否在登录页、是否在区服选择页，
以及登录页按钮中心和目标区服在列表中的位置。

它明确不负责：点击操作（属于 UI 控制器的 `controller.login`）、启动流程的分支与"需要更新"的
报错（属于 dispatch 处理器）、页面导航与到达确认（属于导航器）。

模块的状态与资源所有权：

- 识别事实由调用方传入的 `ContextHandle` 持有（截图事实），模块自身无状态；
- 模板由 `page_checker.calibration` 加载，模块不持有缓存；
- 模板路径、识别区域与 OCR 期望文本由 `constants` 持有；
- 识别不到目标时返回事实而不抛业务错误。

## 2. 模块架构

### 2.1 目录树

```text
autowsgr/application/ui/navigation/page_checker/login_checker/
├── __init__.py        # 模块入口：导出八个识别入口
├── checker.py         # 八个公开识别入口的编排
├── recognition.py     # 模板匹配、OCR 与区服定位，垂直调用 common.vision
└── constants.py       # 模板命名空间、模板文件名、识别区域与期望文本
```

模板资源位于 `resources/image/application/ui/navigation/page_checker/login/`（目录小写、文件名全大写）。

### 2.2 文件职责

| 文件 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| `__init__.py` | 导出八个识别入口 | 业务实现 |
| `checker.py` | 入口编排与参数转发 | 识别细节、读文件、点击 |
| `recognition.py` | 调 `common.vision` 前识别、解释匹配结果、区服定位 | 读文件、组装页面结论、点击 |
| `constants.py` | 模板命名空间、4 个模板文件名、6 个识别区域与 3 组期望文本 | 识别阈值、判定规则、点击坐标 |

### 2.3 依赖方向

```text
导航器 / dispatch 启动流程
        ↓
login_checker（模块入口）
        ↓
login_checker.checker
        └──→ login_checker.recognition ──→ constants
                                       └──→ page_checker.calibration → common.vision
```

禁止方向：

- 不执行点击、不计算路由、不向处理器上报业务错误；
- 不反向依赖 UI 控制器（点击与落点在 `controller.login`）；
- `constants` 只放模板路径、识别区域与期望文本，不放阈值和判定规则；
- 阈值（`_TEMPLATE_CONFIDENCE`）与单帧探测次数留在 `recognition.py`，不下沉 `constants`。

### 2.4 公开出口策略

稳定出口只有模块入口 `login_checker` 导出的八个识别入口；`recognition` 与 `constants` 只对同包内
可见，它们的私有函数与具体常量不得作为跨模块契约。

## 3. 能力总览

| 能力 | 对外入口 | 所在文件 | 输入 | 输出/副作用 | 负责内容 | 不负责内容 |
| --- | --- | --- | --- | --- | --- | --- |
| 健康游戏提示识别 | `login_checker.check_black_screen` | `checker.py` | `ctx` | `bool`；登记最新截图 | 全屏模板判断是否停在该画面 | 点击、判断是否该等待 |
| 更新提示识别 | `login_checker.check_update_prompt` | `checker.py` | `ctx` | `bool`；不修改外部状态 | OCR 判断是否出现"有新的内容需要更新" | 报错、自动更新 |
| 加载中识别 | `login_checker.check_loading` | `checker.py` | `ctx` | `bool`；不修改外部状态 | OCR 判断是否出现"正在进入港区" | 等待、超时处理 |
| 登录页识别 | `login_checker.check_login_page` | `checker.py` | `ctx` | `bool`；不修改外部状态 | 进入游戏模板或换区入口任一命中 | 点击、判断区服 |
| 区服选择页识别 | `login_checker.check_server_select` | `checker.py` | `ctx` | `bool`；不修改外部状态 | 切换大区模板命中 | 点击区服条目 |
| 区服定位 | `login_checker.find_server_position` | `checker.py` | `ctx`、区服名 | 位置序号或 `None` | 四条区域逐条 OCR 比对 | 点击、判断换区成功 |
| 区服序号映射 | `login_checker.server_index` | `checker.py` | 区服名 | 位置序号 | 返回固定位置，OCR 失败时兜底 | 识别、点击 |
| 进入游戏按钮中心 | `login_checker.read_enter_button_center` | `checker.py` | `ctx` | 归一化中心或 `None` | 给出按钮中心供点击 | 点击、确认已进入主页 |
| 换区入口中心 | `login_checker.read_switch_entry_center` | `checker.py` | `ctx` | 归一化中心或 `None` | 给出入口中心供点击 | 点击、确认列表出现 |
| 模板加载 | `page_checker.calibration.load_module_template` | `page_checker/calibration.py` | 命名空间、文件名、名称 | `Template`；读模板文件 | 按命名空间加载模板 | 识别、缓存策略 |

## 4. 启动阶段画面识别

### 4.1 能力说明

三个入口对应启动阶段的三类画面事实：健康游戏提示（黑屏全屏模板）、更新提示（OCR）、
加载中（OCR）。默认是**单帧探测**（`attempts=1`），只回答"这一帧是不是该画面"；调用方需要等待
时传 `absent` / `attempts` / `interval_seconds`，参数原样透传给 `common.vision`——等待与分支由
dispatch 处理器编排，checker 不替它决定耐心。

更新提示与加载中共用同一条底部横幅区域（`PROGRESS_TEXT_ROI`），靠期望文本区分。
不识别"更新中"画面：动态进度条无法稳定判断，更新一律交用户手动处理。

### 4.2 稳定入口

```text
login_checker.check_black_screen(ctx, *, absent=False, attempts=1, interval_seconds=0.5) -> bool
login_checker.check_update_prompt(ctx, *, absent=False, attempts=1, interval_seconds=0.5) -> bool
login_checker.check_loading(ctx, *, absent=False, attempts=1, interval_seconds=0.5) -> bool
```

### 4.3 调用示例

```python
from autowsgr.application.ui.navigation.page_checker import login_checker

if login_checker.check_update_prompt(ctx):
    # 有更新：交 dispatch 处理器报错，checker 只给事实
    ...
```

### 4.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 画面特征未命中 | 返回识别事实 | `False` | 启动流程处理器（决定等待或继续） |
| 模板文件缺失 | 拒绝加载 | `FileNotFoundError` | 交付期修正 |
| 设备或 Context 异常 | 继续向上抛出 | 设备/Context 异常 | 启动流程处理器 |

### 4.5 维护规则

换分辨率或换素材时改 `constants` 的 `BLACK_SCREEN_TEMPLATE`/`UPDATE_PROMPT_ROI`/`PROGRESS_TEXT_ROI`
与对应模板文件；OCR 期望文本变化时改 `UPDATE_PROMPT_TEXT`/`LOADING_TEXT`。启动分支不在这里，
不要为了"等久一点"给这三个入口加 `attempts`。

## 5. 登录页识别

### 5.1 能力说明

进入游戏按钮与"点击换区"入口**二选一命中**即算在登录页：两个模板在同一画面实测 score 均为
1.000，任一可见都说明登录页已经加载完成。

### 5.2 稳定入口

```text
login_checker.check_login_page(ctx, *, absent=False, attempts=1, interval_seconds=0.5) -> bool
```

### 5.3 调用示例

```python
if login_checker.check_login_page(ctx):
    # 点进入游戏或换区（点击由 controller.login 执行）
    ...
```

### 5.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 两个模板都没命中 | 返回识别事实 | `False` | 导航器 / 启动流程处理器 |

### 5.5 维护规则

新增登录页特征时在 `recognition.is_login_page_visible` 的模板序列与 `constants` 同步添加；
判定保持"任一命中"，收紧为"全部命中"会漏判换区状态。

## 6. 区服选择页识别

### 6.1 能力说明

用"切换大区"按钮模板做前识别，命中即说明区服列表已经打开。四个区服名只作为定位依据，
不参与本入口判定。

### 6.2 稳定入口

```text
login_checker.check_server_select(ctx, *, absent=False, attempts=1, interval_seconds=0.5) -> bool
```

### 6.3 调用示例

```python
if login_checker.check_server_select(ctx):
    index = login_checker.find_server_position(ctx, "昆西")
```

### 6.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 切换大区模板未命中 | 返回识别事实 | `False` | 导航器 |

### 6.5 维护规则

区服选择页样式变化时改 `constants.SWITCH_SERVER_ROI` 与 `SWITCH_SERVER_TEMPLATE`。

## 7. 区服定位

### 7.1 能力说明

区服列表固定不滚动，因此拿目标区服名对四条区域各问一次真假，命中即为位置序号（0 起）。
顺序固定：0 胡德 / 1 俾斯麦 / 2 昆西 / 3 长春。

### 7.2 稳定入口

```text
login_checker.find_server_position(ctx: ContextHandle, name: str) -> int | None
login_checker.server_index(name: str) -> int
```

`name` 取值见 `constants.SERVER_NAMES`；单帧探测，逐条比对，命中即返回。

### 7.3 调用示例

```python
index = login_checker.find_server_position(ctx, "俾斯麦")   # 0-3 或 None
```

### 7.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 四条区域都不匹配 | 返回定位失败 | `None`（记 `WARNING`） | 导航器（不点击或另行处理） |
| 命中 | 返回序号 | `int`（记 `INFO`） | 导航器（交给控制器点击） |

### 7.5 维护规则

区服列表增删或顺序变化时同时改 `constants.SERVER_NAMES` 与 `SERVER_NAME_ROIS`，
并同步 `controller.login.constants.SERVER_POSITIONS`（点击落点是同一份数据的另一种表示）。

## 8. 登录页按钮中心

### 8.1 能力说明

回答"按钮现在在哪"，供控制器点击：命中模板时返回归一化中心，未命中返回 `None`。
中心取自 `common.vision.expect_template_center`，是匹配到的模板实际中心，不是搜索区域中心。

### 8.2 稳定入口

```text
login_checker.read_enter_button_center(ctx: ContextHandle) -> tuple[float, float] | None
login_checker.read_switch_entry_center(ctx: ContextHandle) -> tuple[float, float] | None
```

### 8.3 调用示例

```python
page = LoginPage(ctx)
page.click_enter_game(login_checker.read_enter_button_center(ctx))   # 为空时控制器用固定落点
```

### 8.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 模板命中 | 返回中心 | `tuple[float, float]` | 导航器（传给控制器点击） |
| 模板未命中 | 返回空值 | `None` | 导航器（交给控制器用固定落点兜底） |

### 8.5 维护规则

按钮中心随模板位置变化，不要在这里写固定坐标：落点兜底属于控制器（`controller.login.constants`）。

## 9. 统一配置

本模块无运行时配置。

模板命名空间、模板文件名、识别区域与期望文本都是代码常量：它们必须与模板文件和游戏版本同步，
做成用户配置只会让资源与代码版本脱节。

## 10. 错误约定

模块不定义错误类型，也不上报识别错误：

| 场景 | 行为 | 异常 | 处理者 |
| --- | --- | --- | --- |
| 识别不到目标 | 返回识别事实 | 无 | 导航器 / 启动流程处理器决定重试、报错或换路 |
| 模板文件缺失 | 拒绝加载 | `FileNotFoundError` | 交付期修正 |
| 设备或 Context 异常 | 继续向上抛出 | 设备/Context 异常 | 导航器 |

"需要更新"不是本模块的错误：`check_update_prompt` 只返回事实，报错与后续处置由 dispatch 处理器
决定（用户 2026-10-11 定）。

## 11. 日志约定

- 日志对象：`get_logger('ui.login_checker')`（只有 `recognition.py` 记录，`checker.py` 只转发）；
- 级别：画面事实与中心读取用 `DEBUG`；区服定位命中用 `INFO`，未命中用 `WARNING`；
- 格式：`[UI] 登录识别 → 动作：名={!r}`。

| 位置 | 记录内容 |
| --- | --- |
| `登录识别` | 健康游戏提示、更新提示、加载中、登录页、区服选择页各自的命中结果 |
| `登录识别` | 进入游戏按钮中心与换区入口中心的读取结果 |
| `登录识别` | 区服定位命中（`INFO`）或失败（`WARNING`） |

不记录原始截图与完整 OCR 文本。

## 12. 公开出口和调用边界

### 12.1 稳定出口

| 出口 | 来源 | 调用者可以做什么 | 调用者不能做什么 |
| --- | --- | --- | --- |
| `login_checker.check_black_screen` | `checker.py` | 判断是否停在健康游戏提示 | 期望它等待画面消失 |
| `login_checker.check_update_prompt` | `checker.py` | 判断是否出现更新提示 | 期望它报错或自动更新 |
| `login_checker.check_loading` | `checker.py` | 判断是否正在加载 | 期望它等到加载结束 |
| `login_checker.check_login_page` | `checker.py` | 判断是否在登录页 | 期望它区分是哪种进入方式 |
| `login_checker.check_server_select` | `checker.py` | 判断区服列表是否打开 | 期望它给出当前选中区服 |
| `login_checker.find_server_position` | `checker.py` | 读目标区服的位置序号 | 用它点击（点击归控制器） |
| `login_checker.read_enter_button_center` | `checker.py` | 读进入游戏按钮中心 | 期望它保证点击成功 |
| `login_checker.read_switch_entry_center` | `checker.py` | 读换区入口中心 | 期望它保证点击成功 |

`check_login_page` 与 `check_server_select` 同时注册在导航器的到达确认表里，
供 `PageName.LOGIN_PAGE` / `PageName.SERVER_SELECT` 使用。

### 12.2 内部内容

`recognition` 的读取实现、`constants` 的具体常量与 `Template` 加载细节都是内部实现。
测试直接调用它们不使其成为生产出口。

## 13. 模块维护方法

### 13.1 换样本或换分辨率

1. 替换 `resources/image/application/ui/navigation/page_checker/login/` 下的模板文件（文件名保持全大写）；
2. ROI 变化时改 `constants` 中的识别区域，坐标精度与取整方向按 `[规范]python-code-style.md` §6.5 执行；
3. 用干净截图重新确认四个模板的自匹配分数与"两个登录页模板同画面命中"的前提。

### 13.2 新增画面识别

按现有入口的样子增加：`recognition` 加读取函数（模板与区域进 `constants`）、`checker` 加入口、
模块入口导出、补 focused 单测，最后更新本文件的 §3 与对应能力章节。

### 13.3 与其它 checker 保持一致

本模块与 `home_checker`、`sortie_checker` 使用同一套结构：阈值放 `recognition.py`、坐标与模板路径放
`constants.py`、日志用 `[UI] 位置 → 动作：名={!r}`。坐标精度按 `[规范]python-code-style.md` §6.5，
分区线宽度按同规范第 10 节。

### 13.4 修改公开契约

同步更新能力总览、对应能力章节、公开出口表和实现基线。

## 14. 验收门禁

| 检查 | 现状 |
| --- | --- |
| 模块入口 import smoke | 通过 |
| 注册到导航器到达确认表（`test_navigation.py`） | 覆盖（断言 `LOGIN_PAGE` / `SERVER_SELECT` 的确认入口） |
| 四个模板与自匹配分数 | 用户实测（进入游戏与换区模板在同一画面均为 1.000） |
| OCR 期望文本 | 用户实测（更新提示 8 字、加载中 6 字、四个区服名全部一致） |
| 模块专属 pytest（`testing/ui/page_checker/test_login_checker.py`） | 11 项通过：参数透传、默认单帧、定位入口不接收节奏参数 |
| 真图静态验证 | 无对应 `e2e` case（登录阶段需要启动流程，暂未建立） |
| 未验证项 | 实机启动链路（依赖启动流程与初始化重写） |
| 用户验收 | 通过（2026-10-11） |
