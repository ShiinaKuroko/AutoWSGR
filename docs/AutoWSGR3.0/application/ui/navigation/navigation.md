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

**注册表只维护「能去哪、怎么去、到了吗」**：坐标与点击细节在 `controller`，识别细节在 `checker`，
算路与执行在 `service` / `executor`。一条边就是一行数据，不为边写转发函数。

## 3. 接一个新页面：照着做

四步，缺一不可：

1. **`types.py` 的 `PageName` 加一个成员**（值写成中文页面名，跟日志一致）；
2. **写 checker**：`checker/` 下新建或在已有 checker 里加一个入口（写法见 §8）；
3. **注册确认**：`_PAGE_CHECKERS[PageName.XXX] = checker 的入口`；
4. **注册边**：至少一条**入边**（否则永远到不了）和一条**出边**（否则进去出不来）。

### 完整示例：把「演习页」接进来

```python
# 1) types.py
class PageName(StrEnum):
    ...
    EXERCISE = '演习页面'          # 已存在，示例里直接复用

# 2) checker/sortie/checker.py —— 识别入口
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
    PageName.EXERCISE: sortie.check_exercise_page,
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
  ② 起点即目标 → 短路（回主页必经浮窗链，见 §7）
  ③ find_path()          BFS 在可达表上找最短路径；到不了就抛 NavigationError
  ④ walk_forward()       逐边执行，每跳顺序见下
```

每跳的固定动作（`executor.walk_forward`）：

```text
边的 action（一次点击）
  → 离开确认：旧页标志应消失（后识别，absent=True）
  → 到达确认：新页标志应出现（前识别）；这一跳带了 tab 时改走 §6 的分支
  → 压栈
```

「点一下」天然成对，所以这个判断由执行器统一负责，**边和 checker 都不用各自声明**。
边可以声明 `confirm=False` 跳过到达确认——见 §7 的浮窗链。

## 6. 页面内标签（tab）

有些页面内部用标签切换视图：出征页 5 个（出征 / 演习 / 远征 / 战役 / 决战）、
建造页 4 个、升级页 3 个。**标签不是页面。**

### 6.1 建模

- **`PageName` 只表达页面本身**（如 `SORTIE_MAP`），不拆到标签；
- **标签是「到达这一页之后落在哪个视图上」**，作为 `navigate_to` 的入参传入：
  `navigate_to(PageName.SORTIE_MAP, tab='exercise')`；
- **标签的「怎么点、怎么确认」登记在 `registry._TABS`**，每项三个字段：点击动作、确认入口、说明。

### 6.2 到达确认的分支

| 这一跳 | 到达确认 |
| --- | --- |
| **没传 tab** | 用目标页面自己的 checker |
| **传了 tab** | ① 等页面加载（`_TAB_SETTLE_SECONDS`）② 点该标签 ③ 用**标签的 checker** 确认（带重试） |

**传了 tab 时页面级 checker 不参与**——切到别的标签之后，认「默认标签激活」的页面级 checker
本来就该失败，两者互斥。

### 6.3 为什么点标签前要等一下

点页面入口之后，页面本身还在切换动画里；此时点标签会落空。
执行器在**离开确认通过之后、点标签之前**等 `_TAB_SETTLE_SECONDS`（2 秒），再点、再验。

这样不必「点空就重试点击」，也不必因为点早了白白触发一次 SL。
等待时长放在执行器（流程时序），不放 `constants.py`（校准数据）。

### 6.4 为什么不是「标签当页面」

标签当页面会让边变成 O(n²)：四个标签就多出 12 条互切边加 4 条回边，三个页面接近 21 条。
而「每步都要确认」又不允许把标签降级成纯参数——切完无从验证。

`_TABS` 把两者都保住：**边只有「进页 + 回页」两条，标签的确认一点不少。**

## 7. 每日浮窗：一条固定链

浮窗不是 `service` 里的私有流程，而是几个普通页面 + 几条普通边：

| `PageName` | 画面 |
| --- | --- |
| `HOME_NEWS` | 主页 + 每日公告浮窗 |
| `HOME_REWARD` | 主页 + 每日奖励（签到）浮窗 |
| `HOME_REWARD_CONFIRM` | 奖励领取后的确认浮窗 |

```text
每日公告 → 每日奖励 → 每日奖励确认 → 主页
```

**每一步都「先问 checker 再做」**：浮窗不在就什么都不做，避免空点。

**除了链尾，所有边都 `confirm=False`**，分两种：

- **进链的边**（登录页 / 出征页 / 活动地图 → 主页）：不管有没有浮窗，进了主页就算到；
- **链内的中间步**：它们的「到没到」取决于下一个浮窗在不在，静态判不了。

只有链尾「每日奖励确认 → 主页」做真确认——那里才知道主页是否真的干净了。
（实测踩过：进链的边若照常确认，当天公告已关时会直接失败并触发 SL。）

`check_home_page` 因此定义为「**没有浮窗的主页**」：主页模板命中，且三个浮窗都不在。
有浮窗时它返回假，「当前页」会落在对应的浮窗页上，于是 `navigate_to(HOME)` 自然走这条链。

所有原本指向 `HOME` 的边都改成指向 `HOME_NEWS`，这样「从活动页回家」也会顺手把浮窗清掉。

**已知边界**：浮窗目前只弹在主页，所以「有浮窗 ≈ 在主页」这个简化成立；
哪天非主页也弹浮窗，需要重新设计（例如引入浮窗栈）。

## 8. 写一个 checker 的规矩

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

目录职责（`checker/<页面>_checker/`）：`checker.py` 编排识别并返回事实，`recognition.py` 读画面事实，
`constants.py` 只放静态校准数据（ROI、模板名、文本），`__init__.py` 只导出。

## 9. 常见维护任务速查

| 想做什么 | 改哪里 |
| --- | --- |
| 接一个新页面 | `PageName` + checker + `_PAGE_CHECKERS` + `_NAV_TARGETS`（§3 四步） |
| 加一条路径 | `_NAV_TARGETS`（记得补反方向） |
| 改某条边的落点 | 该边 `action` 调用的 `controller` 入口 |
| 调某页的识别节奏 | 该 checker 的默认参数，或调用方 `navigate_to` 时传参 |
| 某个页面认不出来了 | 该 checker 的 `recognition.py` 与 `constants.py`（先核对 ROI 是否比模板大 1px） |
| 加一个每日浮窗 | `PageName` + checker + 在浮窗链里插一条边（`confirm=False`），见 §7 |
| 改浮窗点击落点 | `controller/home/main_page` 的对应入口 |
| 改「什么算干净的主页」 | `home.check_home_page` |
| 改启动段（黑屏/更新/加载） | `service.navigate_to_login` |
| 加一种导航错误 | `types.py` |
| 改「什么时候启动、什么时候 SL」 | `dispatch/startup.py`（**不在这里**） |

## 10. 调试与验证

| 手段 | 位置 |
| --- | --- |
| 单测（替身接管点击与确认） | `testing/ui/navigation/test_navigation.py` |
| 实机 E2E | `python tools/debug_toolkit/main.py e2e <case>` |
| 逐边日志 | `[UI] 导航执行 → 前进/后退：edge=...`，以及离开/到达确认结果 |
| 算路失败 | 日志 `没有从 X 到 Y 的可达路径`，说明 `_NAV_TARGETS` 缺边 |
| 到达确认失败 | 日志 `到达确认失败：边说明`，说明目标页 checker 没认出来（先查 ROI） |

## 11. 边界

**不做**：页面坐标与校准数据、OCR 参数、业务流程、进程生死（拉起 / 强杀）、任务恢复决策。

**不依赖**：dispatch 的处理器与任务队列、任何业务域；设备能力只经 `ctx.runtime.ctrl` 的公开入口。

**与 dispatch 的分工**：dispatch 决定何时启动、何时 SL、按配置决定是否换区；导航器负责识别与点击。
因此 **dispatch 的代码里不出现任何 checker 调用**。

## 12. 当前导航图（2026-10-12）

**已接入**：9 个页面、12 条边（`PageName` 有成员 + `_PAGE_CHECKERS` 有注册 + `_NAV_TARGETS` 有边）。

| 页面 | `PageName` | 识别入口 |
| --- | --- | --- |
| 登录页 | `LOGIN_PAGE` | `login.check_login_page` |
| 区服选择页 | `SERVER_SELECT` | `login.check_server_select` |
| 主页（**不含浮窗**） | `HOME` | `home.check_home_page` |
| 每日公告浮窗 | `HOME_NEWS` | `home.check_home_news_page` |
| 每日奖励浮窗 | `HOME_REWARD` | `home.check_home_reward_page` |
| 奖励确认浮窗 | `HOME_REWARD_CONFIRM` | `home.check_home_reward_confirm_page` |
| 出征页 | `SORTIE_MAP` | `sortie.check_sortie_page` |
| 活动地图 | `EVENT_MAP` | `stage_push.check_event_map_page` |
| 活动章节浮窗 | `EVENT_STAGE_OVERLAY` | `stage_push.check_event_sortie_prepare` |

```text
登录页面 → 区服选择页面
登录页面 → 每日公告弹窗        confirm=False
区服选择页面 → 登录页面        收区服名，位置内部现算
主页面 → 出征页面
主页面 → 活动页面
出征页面 → 每日公告弹窗        confirm=False
活动页面 → 每日公告弹窗        confirm=False
活动页面 → 活动章节浮窗
活动章节浮窗 → 活动页面
每日公告弹窗 → 每日奖励弹窗     confirm=False
每日奖励弹窗 → 每日奖励确认     confirm=False
每日奖励确认 → 主页面          链尾做真确认
```

**尚未接入**（`PageName` 里有名字，但没进门）：

| 情况 | 页面 |
| --- | --- |
| checker 已存在、只是没注册 | `EXERCISE`、`EXPEDITION`、`CAMPAIGN`、`DECISIVE_BATTLE` |
| 连 checker 都还没有 | `SIDEBAR`、`MISSION`、`BACKYARD`、`BATH`、`CANTEEN`、`BUILD`、`INTENSIFY`、`FRIEND`、`SHIP_SELECTION`、`BATTLE_PREPARATION` |

对未接入的页面调 `navigate_to` 会抛「没有可达路径」——**不是坏了，是还没接**，按 §3 四步补上即可。

**程序运行期状态**（`dispatch/session.py`）：

| 字段 | 用途 | 生命周期 |
| --- | --- | --- |
| `_pages` | 导航栈，只保留最近 8 层（`_MAX_PAGES`） | 进程级；SL 后清空 |
| `_server_selected` | 本次运行是否已换过区 | 进程级；SL 后**保留** |

## 13. 变更记录

| 日期 | 变更 |
| --- | --- |
| 2026-10-12 | 新增 §6 页面内标签：标签不是页面，作为 `navigate_to` 入参；执行器到达确认分两支
| | （没传 tab 用页面 checker，传了 tab 先等 2 秒、点标签、再用标签的 checker 确认）；
| | 说明为什么不用「标签当页面」（O(n²) 条边）以及为什么点标签前要等 |
| 2026-10-12 | 重写为维护视角：以注册中心为核心，补「接新页面四步 + 完整示例」与维护速查表 |
| 2026-10-12 | 新增当前导航图：9 个已接入页面、12 条边、未接入清单与进程级状态字段；
| | 记录 `PageName` 语义统一（`BATTLE_PREP`→`BATTLE_PREPARATION`、`CHOOSE_SHIP`→`SHIP_SELECTION`、删 `CHOOSE_REPAIR`） |
| 2026-10-12 | 新增每日浮窗链：三个浮窗页 + `confirm=False` 的中间步 + 回主页边改指向公告；
| | 每跳由五步改为四步（到达前钩子已移除） |
