# application-ui-navigation-home-checker 架构说明

版本：AutoWSGR-3.0 第 1 版
状态：生效
适用范围：`autowsgr/application/ui/navigation/page_checker/home_checker`
实现基线：`codex/20260913-shiinaskuya-upgrade-7b3e`，2026-10-10

## 1. 模块定位

home checker 是 **application 层导航器**的主页识别模块。它只负责把画面读成主页事实：
当前是否在主页、主页上出现了哪种每日浮窗、公告勾选框处于什么状态。

它明确不负责：点击操作（属于 UI 控制器的 `home.main_page.operations`）、浮窗处理流程与页面
导航流程（属于导航器的流程层，尚未建立）、识别失败后的报错与恢复（属于拥有恢复策略的导航器）。

模块的状态与资源所有权：

- 识别事实由调用方传入的 `ContextHandle` 持有（截图事实），模块自身无状态；
- 模板由 `page_checker.calibration` 加载，模块不持有缓存；
- 模板路径与识别区域由 `constants` 持有；
- 错误只使用调用参数校验，识别不到目标时返回事实而不抛业务错误。

## 2. 模块架构

### 2.1 目录树

```text
autowsgr/application/ui/navigation/page_checker/home_checker/
├── __init__.py        # 模块入口：导出四个识别入口与浮窗事实模型
├── checker.py         # 主页浮窗事实模型 HomeNewsOverlay + 四个识别入口
├── recognition.py     # 模板匹配与事实读取，垂直调用 common.vision
└── constants.py       # 模板命名空间、模板文件名、识别区域
```

模板资源位于 `resources/image/application/ui/navigation/page_checker/home/`（目录小写、文件名全大写）。

### 2.2 文件职责

| 文件/目录 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| `__init__.py` | 导出四个入口与 `HomeNewsOverlay` | 业务实现 |
| `checker.py` | 入口编排、公告事实组装、事实模型定义 | 识别细节、读文件、点击 |
| `recognition.py` | 调 `common.vision` 前识别、解释匹配结果 | 读文件、组装页面结论、点击 |
| `constants.py` | 模板命名空间、模板文件名、6 个识别区域 | 识别阈值、判定规则、点击坐标 |

### 2.3 依赖方向

```text
导航器 / 上层调用者
        ↓
home_checker（模块入口）
        ↓
home_checker.checker
        └──→ home_checker.recognition ──→ constants
                                       └──→ page_checker.calibration → common.vision
```

禁止方向：

- 不执行点击、不计算路由、不向处理器上报业务错误；
- recognition 只接收 `ContextHandle`，不读取文件、不持有缓存；
- 本模块不反向依赖 UI 控制器（点击与点击坐标在 `home.main_page`）；
- `constants` 只放模板路径与识别区域，不放阈值和判定规则。

### 2.4 公开出口策略

稳定出口只有模块入口 `home_checker` 导出的四个识别入口和 `HomeNewsOverlay`。
`recognition` 与 `constants` 只对同包内可见；它们的私有函数与具体常量不得作为跨模块契约。

## 3. 能力总览

| 能力 | 对外入口 | 所在文件 | 输入 | 输出/副作用 | 负责内容 | 不负责内容 |
| --- | --- | --- | --- | --- | --- | --- |
| 主页识别 | `home_checker.check_home_page` | `checker.py` | `ctx` | `bool`；登记最新截图 | 判断主页模板是否可见 | 判断是否该清浮窗 |
| 公告浮窗识别 | `home_checker.check_home_news_overlay` | `checker.py` | `ctx` | `HomeNewsOverlay` | 给出浮窗是否在、勾选框状态 | 点击勾选框或关闭公告 |
| 奖励浮窗识别 | `home_checker.check_home_reward_overlay` | `checker.py` | `ctx` | `bool` | 判断奖励浮窗是否存在 | 点击领奖按钮 |
| 奖励确认浮窗识别 | `home_checker.check_home_reward_confirm` | `checker.py` | `ctx` | `bool` | 判断确认浮窗是否存在 | 点击确认按钮 |
| 勾选框中心读取 | `home_checker.read_news_checkbox_center` | `checker.py` | `ctx` | 归一化中心或 `None` | 给出勾选框中心供点击 | 点击、判断浮窗状态 |
| 领奖按钮中心读取 | `home_checker.read_reward_claim_center` | `checker.py` | `ctx` | 归一化中心或 `None` | 给出领奖按钮中心供点击 | 点击、判断浮窗状态 |
| 确认按钮中心读取 | `home_checker.read_reward_confirm_center` | `checker.py` | `ctx` | 归一化中心或 `None` | 给出确认按钮中心供点击 | 点击、判断浮窗状态 |
| 模板加载 | `page_checker.calibration.load_module_template` | `page_checker/calibration.py` | 命名空间、文件名、名称 | `Template`；读模板文件 | 按命名空间加载模板 | 识别、缓存策略 |

## 4. 主页识别

### 4.1 能力说明

用主页入口图标模板在固定区域做前识别，判断当前是否在主页。浮窗打开时会遮挡主页模板，
因此**浮窗态不算在主页**；调用方必须先识别并处理浮窗，再确认主页。

### 4.2 稳定入口

```text
home_checker.check_home_page(ctx: ContextHandle) -> bool
```

- `ctx`：提供设备服务与截图事实的 `ContextHandle`；
- 返回：主页模板命中为 `True`，读不到或浮窗遮挡为 `False`；
- 副作用：按 `common.vision` 约定登记最新截图，不修改页面状态。

### 4.3 调用示例

```python
from autowsgr.application.ui.navigation.page_checker import home_checker

if home_checker.check_home_page(ctx):
    # 已在主页且没有浮窗遮挡
    ...
```

### 4.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 主页模板未命中 | 返回识别事实 | `False` | 导航器（先处理浮窗或换路径） |
| 设备或 Context 异常 | 继续向上抛出 | 设备/Context 异常 | 导航器 |

### 4.5 维护规则

换分辨率或换主页入口图标时只改 `constants.HOME_MAIN_ROI` 与模板文件；判断逻辑不随活动变化。

## 5. 公告浮窗识别

### 5.1 能力说明

一次前识别同时匹配三个模板：公告文字、勾选框已勾选、勾选框未勾选。因此浮窗状态与勾选状态
来自同一帧，调用方不需要二次识别。勾选框只属于公告浮窗，任一模板命中都说明浮窗仍在主页上。

### 5.2 稳定入口

```text
home_checker.check_home_news_overlay(ctx: ContextHandle) -> HomeNewsOverlay
```

`HomeNewsOverlay` 字段：

| 字段 | 含义 |
| --- | --- |
| `matched` | 公告浮窗是否在主页上 |
| `checked` | 勾选框状态；已勾选为 `True`、未勾选为 `False`、没有读到勾选框为 `None` |

### 5.3 调用示例

```python
state = home_checker.check_home_news_overlay(ctx)
if state.matched and state.checked is False:
    # 需要点一次勾选框（点击由 UI 控制器执行）
    ...
```

### 5.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 三个模板都没命中 | 返回识别事实 | `matched=False`、`checked=None` | 导航器（视为没有公告浮窗） |
| 只命中公告文字 | 返回识别事实 | `matched=True`、`checked=None` | 导航器（勾选状态未知） |

### 5.5 维护规则

新增公告状态（例如第二种勾选框样式）时在 `recognition.read_news_overlay` 增加模板与判定，
新模板路径进 `constants`；入口返回值变化必须同步更新本文件 §5.2。

## 6. 奖励浮窗识别

### 6.1 能力说明

用奖励浮窗文字和领取按钮两个模板做前识别，**任一命中即算浮窗存在**：只露出文字说明浮窗正在
弹出，按钮已经可见说明浮窗已经稳定。

### 6.2 稳定入口

```text
home_checker.check_home_reward_overlay(ctx: ContextHandle) -> bool
```

### 6.3 调用示例

```python
if home_checker.check_home_reward_overlay(ctx):
    # 点击领取按钮（点击由 UI 控制器执行）
    ...
```

### 6.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 两个模板都没命中 | 返回识别事实 | `False` | 导航器（视为没有奖励浮窗） |
| 只命中文字或只命中按钮 | 返回识别事实 | `True` | 导航器 |

### 6.5 维护规则

判定语义从"两个都命中"改成"任一命中"是有意选择；若要收紧为必须同时命中，改
`recognition.is_reward_overlay_visible` 的 `min_matches` 并同步更新本节。

## 7. 奖励确认浮窗识别

### 7.1 能力说明

用确认按钮模板做前识别，判断每日奖励确认浮窗是否打开。确认浮窗与奖励浮窗会叠加，
两个入口各自独立报事实，先后顺序由导航器流程层决定。

### 7.2 稳定入口

```text
home_checker.check_home_reward_confirm(ctx: ContextHandle) -> bool
home_checker.read_news_checkbox_center(ctx: ContextHandle) -> tuple[float, float] | None
home_checker.read_reward_claim_center(ctx: ContextHandle) -> tuple[float, float] | None
home_checker.read_reward_confirm_center(ctx: ContextHandle) -> tuple[float, float] | None
```

### 7.3 调用示例

```python
if home_checker.check_home_reward_confirm(ctx):
    # 点击确认按钮（点击由 UI 控制器执行）
    ...
```

### 7.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 确认按钮未命中 | 返回识别事实 | `False` | 导航器 |
| 确认浮窗与奖励浮窗同时存在 | 两个入口都返回真 | 各自 `True` | 导航器按顺序处理 |

### 7.5 维护规则

确认浮窗样式变化时只改 `constants.REWARD_CONFIRM_BUTTON_ROI` 与模板文件。

## 8. 统一配置

本模块无运行时配置。

模板命名空间、模板文件名与识别区域都是代码常量：它们必须与模板文件同步变化，做成用户配置
只会让资源与代码版本脱节。

## 9. 错误约定

模块不定义错误类型，也不上报识别错误：

| 场景 | 行为 | 异常 | 处理者 |
| --- | --- | --- | --- |
| 识别不到目标 | 返回识别事实 | 无 | 导航器决定重试、报错或换路 |
| 模板文件缺失 | 拒绝加载 | `FileNotFoundError` | 交付期修正 |
| 设备或 Context 异常 | 继续向上抛出 | 设备/Context 异常 | 导航器 |

`common.vision` 的前识别在重试耗尽后只返回 `satisfied=False`；"读不到就报错"由拥有恢复策略的
导航器负责，本模块不替它决定。

## 10. 日志约定

- 日志对象：`autowsgr.common.system.logger.get_logger`，channel 为 `ui`；
- 级别：全部使用 `DEBUG`，本模块只产生识别事实，没有页面动作；
- 格式：`[UI] 位置 → 动作：名={!r}`，使用 loguru 占位符。

| 位置 | 记录内容 |
| --- | --- |
| `主页识别` | 主页模板是否可见、公告浮窗事实（含勾选状态）、奖励浮窗是否可见、确认浮窗是否可见 |
| `主页浮窗` | 公告浮窗事实的最终组装结果 |

不记录原始截图、设备信息，也不重复记录 `common.vision` 已输出的匹配分数。

## 11. 公开出口和调用边界

### 11.1 稳定出口

| 出口 | 来源 | 调用者可以做什么 | 调用者不能做什么 |
| --- | --- | --- | --- |
| `home_checker.check_home_page` | `checker.py` | 判断是否在主页 | 用它代替浮窗处理 |
| `home_checker.check_home_news_overlay` | `checker.py` | 读取公告浮窗与勾选状态 | 用它点击勾选框或关闭公告 |
| `home_checker.check_home_reward_overlay` | `checker.py` | 判断奖励浮窗是否存在 | 用它点击领取按钮 |
| `home_checker.check_home_reward_confirm` | `checker.py` | 判断确认浮窗是否存在 | 用它点击确认按钮 |
| `home_checker.HomeNewsOverlay` | `checker.py` | 读取公告浮窗事实 | 修改其字段（模型不可变） |

### 11.2 内部内容

`recognition` 的读取实现、`constants` 的具体常量与 `Template` 加载细节都是内部实现。
测试直接调用它们不使其成为生产出口。

## 12. 模块维护方法

### 12.1 换样本或换分辨率

1. 替换 `resources/image/application/ui/navigation/page_checker/home/` 下的模板文件（文件名保持全大写）；
2. ROI 变化时改 `constants` 中的识别区域，坐标精度与取整方向按
   `[规范]python-code-style.md` §6.5 执行；
3. 跑 `e2e --static home_check` 用外挂样本确认四个入口行为不变。

### 12.2 新增浮窗识别

按现有入口的样子增加：`recognition` 加读取函数（模板进 `constants`）、`checker` 加入口、
模块入口导出、补 focused 单测与静态样本，最后更新本文件的 §3 与对应能力章节。

### 12.3 与其它 checker 保持一致

本模块与 `event_checker` 的 `normal` 使用同一套结构：事实模型放 `checker.py` 顶部、阈值放
`recognition.py`、坐标与模板路径放 `constants.py`、日志用 `[UI] 位置 → 动作：名={!r}`。
坐标精度按 `[规范]python-code-style.md` §6.5，分区线宽度按同规范第 10 节。
新增 checker 时照抄这套形状。

### 12.4 修改公开契约

同步更新能力总览、对应能力章节、公开出口表和实现基线。

## 13. 验收门禁

| 检查 | 现状 |
| --- | --- |
| 模块入口 import smoke | 通过 |
| 模块专属 pytest（`testing/ui/page_checker/test_home_checker.py`） | 7 项通过 |
| 公告浮窗勾选 / 未勾选 / 不存在三种事实 | 覆盖 |
| 奖励浮窗"文字或按钮"判定 | 覆盖 |
| 确认浮窗与奖励浮窗各自独立报事实 | 覆盖 |
| 真图静态验证（`e2e --static home_check`） | 12 步通过 |
| 与 event checker 的结构、注释、日志、分区线一致性 | 已核对并通过 |
| 未验证项 | 实机点击链路与浮窗处理流程（依赖导航器流程层，未实现） |
