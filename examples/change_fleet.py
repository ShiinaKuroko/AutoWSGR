"""最小示例 — 修改舰队。

修改第 2 舰队的舰船配置。
"""

# 已迁移到新方法: 导航器入口 (原 autowsgr.business.legacy_ops.goto_page)
from autowsgr.application.ui.legacy import BattlePreparationPage, PageName
from autowsgr.application.ui.navigation import goto_page
from autowsgr.business.combat.fleet import exact_fleet_rules
from autowsgr.dispatch.legacy_scheduler import launch


# 1. 启动 (加载配置 → 连接模拟器 → 启动游戏)
ctx = launch('usersettings.yaml')

goto_page(ctx, PageName.BATTLE_PREP)

page = BattlePreparationPage(ctx)

page.change_fleet(2, exact_fleet_rules(['U-47', 'U-96']))
