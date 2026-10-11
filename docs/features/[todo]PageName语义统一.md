# PageName 语义统一

状态：**已完成**（2026-10-12）：在新导航器框架内执行，结果见下。

所属任务：`20260830-autowsgr-upgrade`

## 执行结果

以 `autowsgr/application/ui/navigation/types.py` 为准，`PageName` 由 24 个成员调整为 **23 个**：

| 动作 | 成员 | 说明 |
| --- | --- | --- |
| 改名 | `BATTLE_PREP` → `BATTLE_PREPARATION` | 去缩写，与 `BattlePreparationPage` 对齐 |
| 改名 | `CHOOSE_SHIP` → `SHIP_SELECTION` | 页面状态用名词，不用动作短语 |
| 删除 | `CHOOSE_REPAIR` | 零调用；它表达的是浴室页上的「选择修理」浮层，不是独立页面状态 |

**枚举值一个字没动**（仍是「出征准备」「选择舰船页面」），所以 `PageName(value)`、注册键与导航状态序列化结果不变。

## 未采纳的原候选

| 候选 | 原因 |
| --- | --- |
| `DECISIVE_BATTLE` → `DECISIVE` | `DECISIVE` 是形容词，单看不像页面名，反而更难懂 |
| `EVENT_MAP` → `EVENT` | `EVENT` 单看像「事件」；同域还有 `SORTIE_MAP`，改后会不一致 |

## 改名后的框架事实

- 类型定义已从旧的 `autowsgr/common/types.py` 迁到 `navigation/types.py`，本文件原描述已过期。
- `Templates.Page.BATTLE_PREP`、`Templates.Bath.CHOOSE_REPAIR` 是**视觉模板名**，与 `PageName` 无关，未改动。
- 新框架下 5 个成员暂无调用方：`EXERCISE`、`EXPEDITION`、`CAMPAIGN`、`FRIEND`。它们是**尚未接入导航图的页面**
  （checker 已存在、边未注册），不是死代码。

## 验证

- import smoke：`PageName` 23 个成员；`BATTLE_PREPARATION` / `SHIP_SELECTION` 取值不变；`CHOOSE_REPAIR` 已不存在。
- `compileall autowsgr/application/ui autowsgr/dispatch` 通过。
- focused pytest（`testing/ui/navigation`、`testing/dispatch`、`testing/ui/page_checker`、`testing/ui/controller`）
  共 136 passed。余下 14 个失败全部在 `testing/dispatch/test_processor.py`，来自旧模块缺口
  （`goto_page`、`CombatPlan`、`common.constants`），与本次改动无关。
