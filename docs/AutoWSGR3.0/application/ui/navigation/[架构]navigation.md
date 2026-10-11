# [架构] 导航器

> 状态：2026-10-12 重写（面向维护）｜对应提交 `cf1955b`
> 关联：`[任务书]导航器重写.md`｜`[任务书]初始化重写.md` §8｜`[规范]ui-code-style.md`

## 1. 这个模块干什么

把「游戏现在在哪个页面」变成「走到哪个页面」，并且**每走一步都能确认走成了**。

一句话概括分界：**它只处理"页面到页面"**。启动画面（黑屏 / 更新 / 加载）不是页面，由
`navigate_to_login` 单独处理；进程生死由 dispatch 处理。

## 2. 注册中心是整个框架的核心

框架已经完备。**要接一个新页面，需要动的只有注册表 + 一个 checker**，别的代码一行都不用改。

注册表在 `registry.py`，配一张页面名表（`types.py`）共三处：

| 位置 | 形状 | 作用 |
| --- | --- | --- |
| `types.py` 的 `PageName` | `StrEnum` | 页面的唯一标识，全局共用 |
| `registry._PAGE_CHECKERS` | `PageName → Callable` | 这一页怎么确认"到了" |
| `registry._NAV_TARGETS` | `PageName → tuple[NavTarget, ...]` | 从这一页能去哪儿、怎么去 |

边是一个不可变数据类：

```python
@dataclass(frozen=True, slots=True)
class NavTarget:
    target: PageName                      # 去哪
    action: Callable[..., None]           # 怎么去：一次点击，签名 action(ctx, **params)
    description: str = ''                 # 给人看的说明，也进日志
```

**注册表只维护「能去哪、怎么去、到了吗」**：坐标与点击细节在 `controller`，识别细节在 `page_checker`，
算路与执行在 `service` / `executor`。一条边就是一行数据，不为边写转发函数。

## 3. 接一个新页面：照着做

四步，缺一不可：

1. **`types.py` 的 `PageName` 加一个成员**（值写成中文页面名，跟日志一致）；
2. **写 checker**：`page_checker/` 下新建或在已有 checker 里加一个入口（写法见 §6）；
3. **注册确认**：`_PAGE_CHECKERS[PageName.XXX] = checker 的入口`；
4. **注册边**：至少一条**入边**（否则永远到不了）和一条**出边**（否则进去出不来）。

### 完整示例：把「演习页」接进来

```python
# 1) types.py
class PageName(StrEnum):
    ...
    EXERCISE = '演习页面'          # 已存在，示例里直接复用

# 2) page_checker/sortie_checker/checker.py —— 识别入口
def check_exercise_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,
    attempts: int = 1,
    interval_seconds: float = 0.5,
) -> bool:
    """确认演习标签是否激活。"""
    return recognition.is_exercise_tab_active(
        ctx, absent=absent, attempts=attempts, interval_seconds=interval_seconds
    )

# 3) registry.py —— 注册确认（注意导出到该 checker 的 __init__）
_PAGE_CHECKERS: dict[PageName, Callable[..., bool]] = {
    ...
    PageName.EXERCISE: sortie_checker.check_exercise_page,
}

# 4) registry.py —— 注册边（示例：首页 ⇄ 演习页）
_NAV_TARGETS: dict[PageName, tuple[NavTarget, ...]] = {
    PageName.HOME: (
        ...,
        NavTarget(
            PageName.EXERCISE,
            lambda ctx, **_: HomePage(ctx).go_to(Target.EXERCISE),
            '首页 → 演习页',
        ),
    ),
    PageName.EXERCISE: (
        NavTarget(
            PageName.HOME,
            lambda ctx, **_: SortiePage(ctx).go_back(),
            '演习页 → 首页',
        ),
    ),
}
```

做完这四步，`navigate_to(PageName.EXERCISE)` 立刻可用——算路、点击、前后确认、压栈全都是现成的。

## 4. 加一条边

只要起点终点都能被认出来，就只是往 `_NAV_TARGETS` 里加一行。两条约定：

- **有来有回**：加了 `A → B`，通常也要有 `B → A`，否则进去出不来（`navigate_back` 也走它）；
- **参数靠 `**params` 透传**：边的 `action` 收 `**params`，`navigate_to(target, **params)` 原样传下去。

需要参数时不要在调用方算好再传结果，而要在**边内部现算**：调用方（dispatch）不能做 OCR。
例如区服那条边收的是**区服名**，位置由 `_server_index` 在边内部定位：

```python
NavTarget(
    PageName.LOGIN_PAGE,
    lambda ctx, **params: LoginPage(ctx).click_server(_server_index(ctx, str(params['server']))),
    '区服选择页 → 登录页',
)
# 调用方：navigate_to(PageName.LOGIN_PAGE, server='胡德')
```

## 5. 一次 navigate_to 怎么跑

```text
navigate_to(target, **params)
  ① _current_page()      栈顶有就用栈顶；栈空则遍历全部 checker 认出当前页
  ② 起点即目标 → 短路（当前在主页时顺带清每日浮窗）
  ③ find_path()          BFS 在可达表上找最短路径；到不了就抛 NavigationError
  ④ walk_forward()       逐边执行，每跳顺序见下
```

每跳固定五步（`executor.walk_forward`）：

```text
边的 action（一次点击）
  → 离开确认：旧页标志应消失（后识别，absent=True）
  → 到达前的上层处理（到主页时清每日浮窗）
  → 到达确认：新页标志应出现（前识别）
  → 压栈
```

「点一下」天然成对，所以这个判断由执行器统一负责，**边和 checker 都不用各自声明**。

## 6. 写一个 checker 的规矩

**签名固定三件套**（导航图会按需覆盖，不传就用默认）：

```python
def check_xxx_page(
    ctx: ContextHandle,
    *,
    absent: bool = False,        # False 判出现（前识别），True 判消失（后识别）
    attempts: int = 1,           # 识别次数，默认只探当前一帧
    interval_seconds: float = 0.5,
) -> bool:
```

**四条硬要求**：

| 要求 | 原因 |
| --- | --- |
| 只读事实，不点击、不导航、不抛业务错误 | 动作归 `controller`，流程归 `service` |
| 节奏默认值写在 checker 签名里 | 注册表不兼职配节奏；特殊调用方自己传参覆盖 |
| ROI 的像素尺寸必须比模板**各边大 1px** | 项目硬规范：换算用截断，等于模板时会小 1px 导致匹配直接失败 |
| 包入口 `__init__.py` 只导出稳定入口 | 上层从包入口导入，不摸 `checker.py` / `recognition.py` |

目录职责（`page_checker/<页面>_checker/`）：`checker.py` 编排识别并返回事实，`recognition.py` 读画面事实，
`constants.py` 只放静态校准数据（ROI、模板名、文本），`__init__.py` 只导出。

## 7. 常见维护任务速查

| 想做什么 | 改哪里 |
| --- | --- |
| 接一个新页面 | `PageName` + checker + `_PAGE_CHECKERS` + `_NAV_TARGETS`（§3 四步） |
| 加一条路径 | `_NAV_TARGETS`（记得补反方向） |
| 改某条边的落点 | 该边 `action` 调用的 `controller` 入口 |
| 调某页的识别节奏 | 该 checker 的默认参数，或调用方 `navigate_to` 时传参 |
| 某个页面认不出来了 | 该 checker 的 `recognition.py` 与 `constants.py`（先核对 ROI 是否比模板大 1px） |
| 改每日浮窗行为 | `service._handle_daily_popup` / `_handle_daily_news` / `_handle_daily_reward` |
| 改启动段（黑屏/更新/加载） | `service.navigate_to_login` |
| 加一种导航错误 | `types.py` |
| 改「什么时候启动、什么时候 SL」 | `dispatch/startup.py`（**不在这里**） |

## 8. 调试与验证

| 手段 | 位置 |
| --- | --- |
| 单测（替身接管点击与确认） | `testing/ui/navigation/test_navigation.py` |
| 实机 E2E | `python tools/debug_toolkit/main.py e2e <case>` |
| 逐边日志 | `[UI] 导航执行 → 前进/后退：edge=...`，以及离开/到达确认结果 |
| 算路失败 | 日志 `没有从 X 到 Y 的可达路径`，说明 `_NAV_TARGETS` 缺边 |
| 到达确认失败 | 日志 `到达确认失败：边说明`，说明目标页 checker 没认出来（先查 ROI） |

## 9. 边界

**不做**：页面坐标与校准数据、OCR 参数、业务流程、进程生死（拉起 / 强杀）、任务恢复决策。

**不依赖**：dispatch 的处理器与任务队列、任何业务域；设备能力只经 `ctx.runtime.ctrl` 的公开入口。

**与 dispatch 的分工**：dispatch 决定何时启动、何时 SL、按配置决定是否换区；导航器负责识别与点击。
因此 **dispatch 的代码里不出现任何 checker 调用**。

## 10. 变更记录

| 日期 | 变更 |
| --- | --- |
| 2026-10-12 | 重写为维护视角：以注册中心为核心，补「接新页面四步 + 完整示例」与维护速查表 |
