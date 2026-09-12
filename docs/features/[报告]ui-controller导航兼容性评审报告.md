# UI Controller 导航兼容性评审报告

主任务：`20260830-autowsgr-upgrade`

日期：2026-09-09

分支：`codex/20260830-autowsgr-upgrade`

工作区：`C:\ShiinaKuroko\01.Project\AutoWSGR\.worktrees\20260830-autowsgr-upgrade`

## 1. 评审范围

本报告按两份 UI Controller/导航规范，检查 Controller 页面进入路径、`go_back`
入口、页面注册、导航图和显式业务路线。本阶段只评审导航兼容性，不改变业务路径、
状态机或多来源准备页的回退策略。

## 2. 当前路径矩阵

| 页面/控制器 | 主要进入路径 | 当前回退/退出 | 评审结论 |
|---|---|---|---|
| `LoginPage` | 游戏冷启动 | 无游戏内父页面 | 流程根节点，无需 `go_back` |
| `HomePage` | 初始化或导航恢复 | 无 | 游戏内根页面，无需 `go_back` |
| `MapPage` | `HOME -> MAP` | `go_back -> HOME` | 路径明确 |
| 普通/战役/演习准备页 | 普通 `MapPage` 面板进入 | `BaseBattlePreparation.go_back -> MAP` | 当前来源匹配 |
| 决战准备页 | 决战地图进入编队 | 继承普通准备页 `go_back -> MAP` | 父页可能应为决战地图，待确认 |
| 活动准备页 | 活动地图出击 | 继承普通准备页 `go_back -> MAP` | 父页应为活动地图，当前路线 TODO |
| `ChooseShipPage` | 准备页点击舰船槽位 | 只有内部等待离开方法，无独立 `go_back` | 缺少明确页面回退入口 |
| `DecisiveBattlePage` | 地图 `MAP -> DECISIVE_BATTLE` | `go_back -> HOME` | 总览页路径明确 |
| `DecisiveMapController` | 决战总览进入地图/准备页 | `go_to_map_page` 处理准备页回退 | 内部控制器，不是独立注册页面 |
| `BaseEventPage` | `HOME -> EVENT_MAP` | `go_back -> HOME` | 活动地图明确，出击后准备回退待补 |
| `BackyardPage` | `HOME -> BACKYARD` | `go_back -> HOME` | 路径明确 |
| `BathPage` / `CanteenPage` | 后院子页面入口 | `go_back -> BACKYARD` | 路径明确，浴室本阶段不改 |
| `SidebarPage` | `HOME -> SIDEBAR` | `close -> HOME` | 覆盖组件，`close` 语义可接受 |
| `BuildPage` / `IntensifyPage` / `FriendPage` | 侧边栏入口 | `go_back -> SIDEBAR` | 路径明确 |
| `MissionPage` | `HOME -> MISSION` | `go_back -> HOME` | 路径明确 |

## 3. 导航图结论

- `COMMON_EDGES` 维护主页到地图、任务、后院、侧边栏和活动的入口。
- `LOGISTICS_EDGES` 维护任务、后院、浴室、食堂、侧边栏及其叶页面回退。
- `COMBAT_EDGES` 维护地图到决战、地图/决战/活动回主页。
- 导航图不包含通用 `BATTLE_PREP` 边。普通、决战、活动准备页的父页面不同，不能用
  一个无来源的 `BATTLE_PREP -> MAP` 覆盖三种模式。
- 普通、战役和决战到澡堂的业务路线由 `navigation.service` 的显式入口负责；活动
  出征到澡堂仍保留 TODO，等待 `BATTLE_PREP -> EVENT_MAP` 路径实现。

## 4. 待确认事项

### 4.1 选船页回退

`ChooseShipPage` 注册了 `CHOOSE_SHIP` 页面检查器，但没有图边或 `go_back`。当前
编队算法通过选择成功后的离开检测和失败时的内部取消动作处理页面终态。后续需要
决定是否提供显式 `go_back`，以及它应返回调用方传入的准备页还是由上下文保存的
模式来源；不能直接添加固定 `CHOOSE_SHIP -> BATTLE_PREP` 边。

### 4.2 多来源准备页回退

`DecisiveBattlePreparationPage` 和活动出征准备页复用 `BaseBattlePreparation.go_back()`，
该方法只验证普通 `MapPage`。这不会影响当前显式的决战暂离路线，但直接调用准备页
回退时可能出现父页识别/栈记录偏差。建议后续由模式控制器提供明确回退动作或将来源
作为显式依赖传入，再同步导航图测试。

## 5. 验证与残余风险

- navigation compileall 和字符串/枚举路径 smoke：通过。
- 导航专项测试：`38 passed`、`3 failed`。
- 3 个失败是既有架构断言，分别错误要求删除页面私有常量、拒绝显式澡堂路线、
  恢复无来源 `BATTLE_PREP -> MAP`；本报告不把它们当作本次修复失败。
- 未执行真实设备导航；选船页回退和模式准备页父页仍需业务来源确认。
