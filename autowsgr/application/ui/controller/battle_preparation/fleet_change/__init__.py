"""模块功能：组织出征准备页面的舰队选船、规划、调整和模式分支。

上层调用：
- application.ui.controller.battle_preparation.preparation：组合换船 Mixin。
- business.combat：传入普通、战役和决战舰队目标。

下层依赖：
- application.ui.controller.battle_preparation：提供准备页截图、槽位和页面操作。
- application.ui.controller.shared.choose_ship：执行选船页面的原子操作。
- application.ui.fleet：提供舰船选择规则和值对象。

舰队选择实现保留在 UI 域，因为它直接操作选船页面并依赖 OCR；本模块不承担 OCR
引擎生命周期管理。

原有职责说明:

统一 "扫描 -> 定点更换 -> 调整次序" 流程,
常规出征与决战共用, 通过 ``_use_search`` 控制是否使用搜索框。

内部模块:

- ``_detect.py`` -- 准备页舰队 OCR 检测
- ``_rules.py`` -- 舰队规则匹配与校验
- ``_planning.py`` -- 目标分配与槽位规划
- ``_selection.py`` -- 船池选择页面操作
- ``_alignment.py`` -- 舰队成员调整与排序
- ``_change.py`` -- 普通/活动/演习换船主流程编排
- ``campaign.py`` -- 战役固定槽位点对点换船
"""

from autowsgr.application.ui.controller.battle_preparation.fleet_change._change import (
    FleetChangeMixin,
)
from autowsgr.application.ui.controller.battle_preparation.fleet_change.campaign import (
    CampaignFleetChangeMixin,
)
from autowsgr.application.ui.controller.battle_preparation.fleet_change.decisive import (
    change_decisive_fleet,
)


__all__ = ['CampaignFleetChangeMixin', 'FleetChangeMixin', 'change_decisive_fleet']
