# fleet main_page 方法迁移台账

## 迁移边界

- 来源：`autowsgr/application/ui/controller/fleet/battle_preparation_page/`
- 目标：`autowsgr/application/ui/controller/fleet/main_page/`
- `shipyard_page` 不接收准备页方法；它只负责船池页面本身的搜索、识别和选船。
- `main_page/page.py` 负责编排完整页面流程和提供稳定调用出口，不实现 OCR、ROI 或具体动作细节。
- 本阶段只做目录归并和入口调整，不改 OCR、ROI、维修、补给或编队算法。

状态说明：`待迁移` 表示源码尚未归并；`已迁移` 表示对应定义已进入 `main_page` 目录；`删除` 表示旧包兼容层不应保留。

## `base.py`

| # | 定义 | 业务语义 | 分类 | 目标 | 状态 |
|---:|---|---|---|---|---|
| 1 | `BaseBattlePreparation.__init__` | 注入设备、配置和 OCR 上下文 | main_page 基础能力 | `main_page/page.py` | 已迁移 |
| 2 | `check_current_page` | 通过准备页模板确认当前页面 | 视觉识别（模板） | `main_page/page.py`，后续归入 recognition 区域 | 已迁移 |
| 3 | `check_auto_supply_enabled` | 通过颜色探测自动补给状态 | OCR/ROI 外的颜色识别 | `main_page/page.py`，后续归入 recognition 区域 | 已迁移 |
| 4 | `read_selected_fleet` | 通过颜色探测当前舰队标签 | OCR/ROI 外的颜色识别 | `main_page/page.py`，后续归入 recognition 区域 | 已迁移 |
| 5 | `read_active_panel` | 通过颜色探测当前底部面板 | OCR/ROI 外的颜色识别 | `main_page/page.py`，后续归入 recognition 区域 | 已迁移 |
| 6 | `select_fleet` | 点击并切换目标舰队 | 纯页面操作 | `main_page/page.py` | 已迁移 |
| 7 | `select_panel` | 点击并切换底部面板 | 纯页面操作 | `main_page/page.py` | 已迁移 |
| 8 | `click_ship_slot` | 点击准备页槽位，进入船池 | main_page 到 shipyard_page 的边界动作 | `main_page/page.py` | 已迁移 |
| 9 | `toggle_auto_supply` | 点击自动补给开关 | 纯页面操作 | `main_page/page.py` | 已迁移 |
| 10 | `open_quick_supply` | 打开快速补给面板 | main_page 组合动作 | `main_page/page.py` | 已迁移 |
| 11 | `open_quick_repair` | 打开快速修理面板 | main_page 组合动作 | `main_page/page.py` | 已迁移 |
| 12 | `start_battle` | 点击开始出征 | 纯页面操作 | `main_page/page.py` | 已迁移 |
| 13 | `try_start_battle` | 出征并确认已经离开准备页 | main_page 流程动作 | `main_page/page.py` | 已迁移 |
| 14 | `go_back` | 退出准备页并返回来源地图 | 页面导航动作 | `main_page/page.py` | 已迁移 |
| 15 | `_preferred_ocr` | 选择增强 OCR 的过渡兼容开关 | 废弃兼容逻辑 | 删除，不迁移 | 删除 |

## `detection.py`

| # | 定义 | 业务语义 | 分类 | 目标 | 状态 |
|---:|---|---|---|---|---|
| 16 | `FleetInfo.to_ships` | 将识别出的舰队信息转换为战斗舰船对象 | 数据转换 | `main_page/detection.py`，后续按领域再评估 | 已迁移 |
| 17 | `detect_ship_damage` | 识别六个槽位的血量状态 | ROI/颜色识别 | `main_page/detection.py`，后续归入 recognition 区域 | 已迁移 |
| 18 | `detect_fleet_info` | 切换舰队并组织等级、血量识别 | main_page 流程编排 | `main_page/detection.py`，由 `page.py` 暴露 | 已迁移 |
| 19 | `_recognize_fleet_levels` | OCR 识别舰船等级 | OCR/ROI 识别 | `main_page/detection.py`，后续归入 recognition 区域 | 已迁移 |
| 20 | `_recognize_fleet_ship_types` | OCR 识别舰种 | OCR/ROI 识别 | `main_page/detection.py`，后续归入 recognition 区域 | 已迁移 |
| 21 | `_best_ship_type_from_results` | 从 OCR 结果筛选唯一舰种 | OCR 结果解析 | `main_page/detection.py`，后续归入 recognition 区域 | 已迁移 |
| 22 | `_parse_level` | 解析等级 OCR 文本 | OCR 结果解析 | `main_page/detection.py`，后续归入 recognition 区域 | 已迁移 |
| 23 | `_best_level_from_results` | 从 OCR 结果筛选最佳等级 | OCR 结果解析 | `main_page/detection.py`，后续归入 recognition 区域 | 已迁移 |

## `supply.py`

| # | 定义 | 业务语义 | 分类 | 目标 | 状态 |
|---:|---|---|---|---|---|
| 24 | `check_support_enabled` | 识别战役支援是否启用或耗尽 | 颜色识别 | `main_page/supply.py`，后续归入 recognition 区域 | 已迁移 |
| 25 | `toggle_battle_support` | 点击切换战役支援 | 纯页面操作 | `main_page/supply.py` | 已迁移 |
| 26 | `supply` | 打开补给面板并点击指定槽位 | main_page 流程动作 | `main_page/supply.py` | 已迁移 |
| 27 | `apply_supply` | 根据自动补给状态决定是否手动补给 | main_page 流程动作 | `main_page/supply.py` | 已迁移 |

## `repair.py` 与 `repair_action.py`

| # | 定义 | 业务语义 | 分类 | 目标 | 状态 |
|---:|---|---|---|---|---|
| 28 | `RepairMixin.check_repair` | 维修流程对外检查入口 | main_page 流程出口 | `main_page/repair.py` | 已迁移 |
| 29 | `RepairMixin.repair_slots` | 对外执行指定槽位维修 | main_page 页面动作出口 | `main_page/repair.py` | 已迁移 |
| 30 | `RepairMixin.apply_repair` | 对外执行检测、维修、复查和重试 | main_page 流程出口 | `main_page/repair.py` | 已迁移 |
| 31 | `repair_action.check_repair` | 根据损伤状态计算维修槽位 | main_page 内部流程 | `main_page/repair_action.py` | 已迁移 |
| 32 | `repair_action.repair_slots` | 点击快速修理面板中的槽位 | main_page 内部页面动作 | `main_page/repair_action.py` | 已迁移 |
| 33 | `repair_action.apply_quick_repair` | 执行快速维修完整流程 | main_page 内部流程 | `main_page/repair_action.py` | 已迁移 |

## `page.py` 与包出口

| # | 定义 | 业务语义 | 分类 | 目标 | 状态 |
|---:|---|---|---|---|---|
| 34 | `BattlePreparationPage` | 组合准备页能力并承载业务可调用流程 | page 流程入口 | `main_page/page.py` | 已迁移 |
| 35 | `prepare_and_start_battle` | 从准备页识别、舰队处理到点击并确认进入战斗 | main_page 完整流程出口 | `main_page/page.py` | 已实现 |
| 36 | `__getattr__` | 旧 `battle_preparation_page` 包的惰性兼容出口 | 迁移后无业务意义 | 删除旧包入口 | 删除 |

## 收口检查

- [x] 旧 `fleet/battle_preparation_page/` 不再包含 Python 源码。
- [x] 所有上层调用改为 `fleet.main_page` 或其子模块。
- [x] `main_page/page.py` 不实现 OCR、ROI、坐标识别或具体维修算法。
- [x] `main_page/__init__.py` 提供 `BattlePreparationPage`、状态类型和 fleet_change 的稳定出口。
- [x] 每个条目的状态更新为 `已迁移` 或 `删除`。
