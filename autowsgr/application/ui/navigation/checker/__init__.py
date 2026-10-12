"""模块功能：承载导航器的各页面检查器实现。

上层调用：
- application.ui.navigation.registry：按页面取用对应的到达确认入口。

边界：只做页面归属，不放识别规则与导航逻辑。
"""

from __future__ import annotations
