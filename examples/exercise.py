"""最小示例 — 刷演习。

使用第 1 舰队自动挑战所有可用对手。
"""

# 已迁移到新方法: 演习执行器兼容入口 (原 autowsgr.ops.ExerciseRunner)
from autowsgr.business.combat.exercise import ExerciseRunner
from autowsgr.scheduler import launch


# 1. 启动
ctx = launch('usersettings.yaml')

# 2. 执行演习
runner = ExerciseRunner(ctx, fleet_id=1)
results = runner.run()

print(f'完成 {len(results)} 场演习')
