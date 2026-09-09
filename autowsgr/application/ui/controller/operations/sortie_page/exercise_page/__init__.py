"""模块功能：提供演习顶部标签的页面控制器和状态模型。

上层调用：
- application.ui.controller.operations.sortie_page.battle_page.page：组合演习面板 Mixin。
- business.combat.exercise：驱动演习对手读取和出征入口。

下层依赖：
- application.ui.controller.operations.sortie_page.exercise_page.page：提供页面行为。
- application.ui.controller.operations.sortie_page.exercise_page.constants：提供页面校准。
"""

from autowsgr.application.ui.controller.operations.sortie_page.exercise_page.page import (
    ExercisePanelMixin,
    ExerciseRivalStatus,
)


__all__ = ['ExercisePanelMixin', 'ExerciseRivalStatus']
