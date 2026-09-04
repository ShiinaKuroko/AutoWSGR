# Combat Application Foundation

`application/combat` 是不可调度的战斗领域基建。它提供一次战斗所需的驱动、动作、
识别、结果记录和规则评估；任务队列、优先级、暂停恢复和导航交接不属于这里。

## 依赖方向

```text
business/*Executor
        ↓ CombatPlan / business CombatEngine
application/combat/
        ├── engine/           状态机驱动与阶段转移
        │   └── phase_handlers.py 通用阶段点击、推进和终态动作
        ├── actions.py        战斗页面物理动作
        ├── recognizer.py     阶段视觉状态识别
        ├── recognition.py    视觉观测适配
        ├── history.py        中立战斗事件和结果记录
        └── node_tracker.py   多节点地图位置追踪
                ↓
        common/calibration → common/vision → common/device
```

`engine` 只负责驱动状态机。它组合其他子系统，但不直接定义坐标、OCR ROI、
页面路径或任务生命周期。`actions` 只产生设备动作；`recognition` 只返回观测；
`phase_handlers` 负责通用阶段推进；业务规则和战果解释留在
`business/combat/handlers.py`。

## 公开入口

跨业务代码只从 `autowsgr.business.combat` 导入业务引擎和计划；通用结果记录位于
`autowsgr.application.combat.history`：

```python
from autowsgr.business.combat import CombatEngine, CombatPlan, CombatResult

result = CombatEngine(
    device,
    ocr,
    stop_requested=stop_requested,
).fight(plan, initial_ship_stats=ship_stats)
```

引擎接收明确的设备、OCR 和停止查询能力，不持有 `GameContext`。`SL` 只返回
`CombatResult`，由上层的重试/初始化策略决定是否重启游戏。

## 校准资源

战斗点击坐标位于 `common/data/calibration/coordinates/combat.yaml`，动作通过
`infra.ui.profile.coordinates.point('combat', key)` 读取。模板、OCR 和地图数据
位于 `common/data`，运行时只读。

## 编队基建

`business/combat/fleet.py` 保存不可变舰船/槽位规则和 YAML/HTTP 入口转换；
`business/fleet_policy.py` 保存普通出征、演习、远征、战役和决战的编队策略。它们
不创建 Executor，也不维护任务状态。

## 最小验证

```text
uv run pytest testing/combat testing/business/combat/exercise -q
uv run python -m compileall -q autowsgr/application/combat autowsgr/business/combat/fleet.py
```
