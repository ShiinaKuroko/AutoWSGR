"""最小示例 — 修改舰队。

修改第 2 舰队的舰船配置。
"""

from autowsgr.combat.fleet import exact_fleet_rules
# 已迁移到新方法: 导航器入口 (原 autowsgr.ops.goto_page)
from autowsgr.business.system.navigate import goto_page
from autowsgr.scheduler import launch
from autowsgr.ui import BattlePreparationPage, PageName


# 1. 启动 (加载配置 → 连接模拟器 → 启动游戏)
ctx = launch('usersettings.yaml')

goto_page(ctx, PageName.BATTLE_PREP)

page = BattlePreparationPage(ctx)

page.change_fleet(2, exact_fleet_rules(['U-47', 'U-96']))
