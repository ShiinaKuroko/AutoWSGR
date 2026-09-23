"""模块功能：导出演习页面控制器和对手状态结果。

上层调用：
- business.combat.exercise：调用演习页面完整业务入口。

下层依赖：
- application.ui.controller.operations.sortie_page.exercise_page.page：提供页面流程和结果类型。

边界：
本包只提供稳定导出，不执行识别、设备操作或页面流程。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.operations.sortie_page.exercise_page.page import (
    ExercisePage,
    ExerciseRivalStatus,
)


__all__ = ['ExercisePage', 'ExerciseRivalStatus']
