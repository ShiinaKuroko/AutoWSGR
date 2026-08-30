# Combat Infrastructure

`infra/combat` 是不可调度的战斗领域基建。它提供一次战斗所需的驱动、动作、
识别、结果记录和规则评估；任务队列、优先级、暂停恢复和导航交接不属于这里。

## 依赖方向

```text
business/*Executor
        ↓ CombatPlan / CombatEngine
infra/combat/
        ├── engine/           状态机驱动、阶段转移与作战计划
        ├── handlers.py       阶段编排与数据采集
        ├── actions.py        战斗页面物理动作
        ├── recognizer.py     阶段视觉状态识别
        ├── recognition.py    敌舰、阵型、战果和掉落识别
        ├── history.py        战斗事件与结果记录
        ├── node_tracker.py   多节点地图位置追踪
        └── rules.py          纯规则评估
                ↓
        infra/ui/profile → infra/vision → infra/emulator
```

`engine` 只负责驱动状态机。它组合其他子系统，但不直接定义坐标、OCR ROI、
页面路径或任务生命周期。`actions` 只产生设备动作；`recognition` 只返回观测；
`handlers` 将当前阶段的观测、规则和动作组合成引擎结果。

## 公开入口

跨业务代码只从 `autowsgr.infra.combat` 导入：

```python
from autowsgr.infra.combat import CombatEngine, CombatPlan, CombatResult

result = CombatEngine(
    device,
    ocr,
    stop_requested=stop_requested,
).fight(plan, initial_ship_stats=ship_stats)
```

引擎接收明确的设备、OCR 和停止查询能力，不持有 `GameContext`。`SL` 只返回
`CombatResult`，由上层的重试/初始化策略决定是否重启游戏。

## 校准资源

战斗点击坐标位于 `infra/data/calibration/coordinates/combat.yaml`，动作通过
`infra.ui.profile.coordinates.point('combat', key)` 读取。模板、OCR 和地图数据
位于 `infra/data`，运行时只读。

## 编队基建

`infra/fleet/model.py` 保存不可变舰船/槽位规则和 YAML/HTTP 入口转换；
`infra/fleet/policy.py` 保存普通出征、演习、远征、战役和决战的编队策略。它们
不创建 Executor，也不维护任务状态。

## 最小验证

```text
uv run pytest testing/combat testing/business/combat/exercise -q
uv run python -m compileall -q autowsgr/infra/combat autowsgr/infra/fleet
```
