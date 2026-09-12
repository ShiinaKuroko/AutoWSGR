# PageName 语义统一

状态：`TODO`，后续单独处理。

所属任务：`20260830-autowsgr-upgrade`

## 当前结论

当前 `PageName` 共 15 个成员。它们是页面状态标识，不等同于页面目录、
Controller 类名、视觉模板名或页面内浮层名。

枚举成员当前为：

```text
HOME、MAP、BATTLE_PREP、SIDEBAR、MISSION、BACKYARD、BATH、CANTEEN、
CHOOSE_REPAIR、BUILD、INTENSIFY、FRIEND、DECISIVE_BATTLE、CHOOSE_SHIP、EVENT_MAP
```

## 已确认保持

- `PageName.HOME` 是主页状态，枚举值“主页面”保持不变；不恢复旧成员 `MAIN`。
- `PageName.MAP` 对应 `MapPage` 的地图/出征区域，当前无需改名。
- `SIDEBAR`、`MISSION`、`BACKYARD`、`BATH`、`CANTEEN`、`BUILD`、`INTENSIFY`
  和 `FRIEND` 已能直接表达业务语义，当前无需改名。
- `Templates.MainPage`、`CommonPage`、`Templates.Bath.CHOOSE_REPAIR` 以及测试目录名
  不属于本台账的机械替换范围。

## 待确认的候选改名

以下只建议修改 Python 成员名，不修改枚举值：

| 当前成员 | 候选成员 | 原因 |
|---|---|---|
| `BATTLE_PREP` | `BATTLE_PREPARATION` | 去除 `PREP` 缩写，与 `BattlePreparationPage` 对齐 |
| `DECISIVE_BATTLE` | `DECISIVE` | 与 `decisive` 页面域和“决战”业务名对齐 |
| `EVENT_MAP` | `EVENT` | 与 `event` 页面域和“活动”业务名对齐 |
| `CHOOSE_SHIP` | `SHIP_SELECTION` | 页面状态使用名词语义，不使用动作短语 |

## `CHOOSE_REPAIR` 边界

`PageName.CHOOSE_REPAIR` 当前没有仓内调用方。实际识别对象是浴室页面上的
“选择修理”浮层，`BathPage.check_current_page()` 仍返回 `PageName.BATH`。

因此不能把它直接改名为另一个页面状态。后续需要单独确认：

1. 是否存在仓外调用方依赖 `PageName.CHOOSE_REPAIR`。
2. 是否删除这个无调用的遗留成员。
3. 如果需要表达浮层，是否放入独立的浮层状态类型，而不是继续放在 `PageName`。

## 处理要求

确认候选映射后再执行以下工作：

1. 同步 `autowsgr/common/types.py` 中的成员名。
2. 同步页面注册表、导航图、运行时、业务、测试、工具和文档调用方。
3. 用原枚举值验证 `PageName(value)`、页面注册键和导航状态序列化结果不变。
4. 不修改 `bath_page`，不顺手处理上下文或 OCR 专题。
5. 完成 focused pytest、compileall、相关 import smoke、scoped pre-commit 和
   `git diff --check`。

## 当前未处理

- 尚未修改任何 `PageName` 成员或调用方。
- 尚未删除或迁移 `CHOOSE_REPAIR`。
- 尚未改变任何页面行为、导航路径或外部字符串契约。
