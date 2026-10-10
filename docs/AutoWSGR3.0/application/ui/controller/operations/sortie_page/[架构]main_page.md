# application-ui-controller-operations-sortie-page-main-page 架构说明

版本：AutoWSGR-3.0 第 1 版
状态：生效
适用范围：`autowsgr/application/ui/controller/operations/sortie_page/main_page`
实现基线：`codex/20260913-shiinaskuya-upgrade-7b3e`，2026-10-11

## 1. 模块定位

这是**出征页页面壳**的单击控制器。出征页是综合页面，靠顶部标签条在五个业务之间切换
（出征 / 演习 / 远征 / 战役 / 决战）。

它只负责两件事：把"切到哪个标签"和"离开出征页"变成一次点击。它明确不负责：标签识别
（属于 `sortie_checker`）、切换确认与等待（属于导航器）、业务页面自身的流程（属于各业务页面）。

模块的所有权：

- 标签落点、返回落点由 `constants` 持有；
- 远征通知探针以**像素签名**形式由 `constants` 持有，识别走 `common.vision.expect_pixels`；
- 点击能力来自 `common.device.service`，通过 `ctx.runtime.ctrl` 垂直调用。

## 2. 模块架构

### 2.1 目录树

```text
autowsgr/application/ui/controller/operations/sortie_page/main_page/
├── __init__.py        # 导出 SortiePage、SortieTab、SORTIE_TAB_LIST 与远征通知识别
├── page.py            # SortiePage：go_to 与 go_back 两个单击
├── constants.py       # 标签落点、返回落点、远征通知像素签名
└── recognition.py     # 远征通知识别（expect_pixels）
```

### 2.2 文件职责

| 文件 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| `__init__.py` | 导出稳定入口 | 业务实现 |
| `page.py` | 标签切换与返回两个单击、`SortieTab` 枚举 | 识别、等待、编排 |
| `constants.py` | 静态落点与像素签名 | 识别逻辑、流程参数 |
| `recognition.py` | 远征通知像素识别 | 点击、导航 |

### 2.3 依赖方向

```text
导航器 / 业务层
        ↓
main_page.SortiePage
        ├──→ main_page.constants（落点与像素签名）
        └──→ common.device.service（经 ctx.runtime.ctrl 点击）

main_page.recognition ──→ common.vision.expect_pixels
```

禁止方向：

- 不 import `sortie_checker`（标签识别归导航器）；
- 不等待页面、不重试、不判断是否切换成功；
- 不做标签识别（旧 `PixelChecker` / 二值化那套已删除）。

### 2.4 公开出口策略

稳定出口是 `SortiePage`、`SortieTab`、`SORTIE_TAB_LIST` 与 `check_expedition_notification`；
`constants` 只服务本模块。

## 3. 能力总览

| 能力 | 对外入口 | 输入 | 输出/副作用 | 负责内容 | 不负责内容 |
| --- | --- | --- | --- | --- | --- |
| 切换标签 | `SortiePage.go_to` | 标签、可选识别中心 | 一次点击 | 查表或按中心点击标签 | 确认是否切换成功 |
| 离开出征页 | `SortiePage.go_back` | 无 | 一次点击 | 点击返回按钮 | 确认是否回到主页 |
| 远征通知识别 | `check_expedition_notification` | `ctx` | `bool` | 像素签名单帧探测 | 领取奖励、页面跳转 |

## 4. 切换标签

### 4.1 能力说明

五个标签位置固定，因此 `constants.TAB_POSITIONS` 可作为兜底；导航器若已从 `sortie_checker`
拿到标签模板中心，则优先使用中心，保证点得准。

### 4.2 稳定入口

```text
SortiePage.go_to(tab: SortieTab, position: tuple[float, float] | None = None) -> None
```

### 4.3 调用示例

```python
from autowsgr.application.ui.controller.operations.sortie_page.main_page import SortiePage, SortieTab

page = SortiePage(ctx)
page.go_to(SortieTab.EXERCISE)              # 用固定落点
page.go_to(SortieTab.EXERCISE, center)      # 用识别中心
```

### 4.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 传入识别中心 | 按中心点击 | 无 | 导航器 |
| 未传中心 | 用固定落点 | 无 | 导航器 |
| 点击后未切换成功 | 控制器不感知 | 无 | 导航器用 `sortie_checker` 确认并决定重试 |

### 4.5 维护规则

标签位置变化时改 `TAB_POSITIONS`；新增业务标签时同时补 `SortieTab` 与落点。

## 5. 离开出征页

### 5.1 能力说明

左上角返回按钮位置固定，点一次即可；是否回到主页由导航器确认。

### 5.2 稳定入口

```text
SortiePage.go_back() -> None
```

### 5.3 调用示例

```python
page.go_back()
```

### 5.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 调用 | 点击一次 | 无 | 导航器负责确认 |

### 5.5 维护规则

返回按钮位置变化时改 `CLICK_BACK`。

## 6. 远征通知识别

### 6.1 能力说明

出征页顶部有远征完成通知时，探针位置会出现橙红色像素。识别用像素签名单帧探测，
不等待、不重试。

### 6.2 稳定入口

```text
check_expedition_notification(ctx: ContextHandle) -> bool
```

### 6.3 调用示例

```python
from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    check_expedition_notification,
)

if check_expedition_notification(ctx):
    ...   # 远征完成，交由业务层决定去收取
```

### 6.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 探针命中 | 返回事实 | `True` | 业务层 |
| 探针未命中 | 返回事实 | `False` | 业务层 |

### 6.5 维护规则

探针位置或通知颜色变化时改 `constants.EXPEDITION_NOTIF_SIGNATURE`（`PixelRule` 的
坐标、颜色、容差）；不要把识别逻辑改回散装像素比较。

## 7. 统一配置

本模块无运行时配置。

## 8. 错误约定

| 场景 | 行为 | 异常 | 处理者 |
| --- | --- | --- | --- |
| 点击本身失败 | 继续向上抛出 | 设备异常 | 导航器 |
| 像素识别失败 | 返回事实 | 无 | 业务层 |

## 9. 日志约定

- 日志对象：`get_logger('ui.sortie_page.main_page')`；
- 级别：点击入口用 `INFO`，像素识别由 `common.vision` 记 `DEBUG`；
- 格式：`[UI] 出征页 → 动作：名={!r}`。

## 10. 公开出口和调用边界

### 10.1 稳定出口

| 出口 | 调用者可以做什么 | 调用者不能做什么 |
| --- | --- | --- |
| `SortiePage` | 构造页面壳单击控制器 | 在控制器里做标签识别或等待 |
| `SortiePage.go_to` | 点目标标签 | 期望它确认切换成功 |
| `SortiePage.go_back` | 点返回 | 期望它确认已回主页 |
| `SortieTab` / `SORTIE_TAB_LIST` | 表达标签与顺序 | 在控制器外改落点 |
| `check_expedition_notification` | 读取远征通知 | 传裸截图（入口只收 `ctx`） |

### 10.2 内部内容

`constants` 的落点与像素签名是实现细节。

## 11. 模块维护方法

### 11.1 切换确认归导航器

控制器只点一次；是否切到目标标签由导航器用 `sortie_checker` 的五个入口确认，
失败重试也在导航器。旧 `click_tab` 里的等待、重试与 `NavigationError` 已随本批删除。

### 11.2 旧通用标签识别已移出

旧 `TabbedPageType` 与二值化标签识别属于"共享标签栏"的通用识别，归导航器持有；
本模块不再承载它。建造 / 强化 / 任务 / 好友四个页面的对应识别等各自重写时另行处理。

### 11.3 修改公开契约

同步更新能力总览、对应能力章节、公开出口表和实现基线。

## 12. TODO：后续工作（未实现）

1. **标签中心坐标**：`sortie_checker` 目前只返回标签是否激活，不返回标签中心；导航器要拿中心
   就得先给 checker 加一个"读标签中心"的入口（`TemplateMatchResult.center` 已具备该能力）。
2. **五个业务页面**：远征 / 出征准备 / 决战入口 / 演习 / 战役五个页面控制器曾继承本模块的
   `SortiePage`，本批重写后需要各自按新形状重写。
3. **活动玩法命名约定**：立体强袭（`dimensional_assault`）、舰队问答（`fleet_quiz`）开工时
   沿用 `event_checker` 的玩法子包约定。

## 13. 验收门禁

| 检查 | 现状 |
| --- | --- |
| 模块入口 import smoke | 通过 |
| 模块专属 pytest（`testing/ui/controller/test_sortie_page.py`） | 7 项通过 |
| 五个标签的固定落点 | 覆盖 |
| 识别中心优先 | 覆盖 |
| 返回落点 | 覆盖 |
| 远征通知（签名 + 单帧探测） | 覆盖 |
| 未验证项 | 实机点击链路（依赖导航器编排） |
