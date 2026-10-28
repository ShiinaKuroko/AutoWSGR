"""模块功能：组织出征相关页面的 UI 控制器。

上层调用：
- application.ui.navigation：获取出征各页面的控制器。

下层依赖：
- application.ui.controller.operations.sortie.battle_preparation：提供出征准备页控制器。

本包只负责目录边界，不聚合导入子页面，也不保存运行时状态。
"""

__all__: list[str] = []
