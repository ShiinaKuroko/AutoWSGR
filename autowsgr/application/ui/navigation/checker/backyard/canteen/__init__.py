"""模块功能：提供餐厅二级页检查器的模块入口。

上层调用：
- application.ui.navigation：调用餐厅二级页的确认入口。

下层依赖：
- canteen.checker：提供识别入口。

本模块只导出稳定入口，不放业务实现。
"""

from __future__ import annotations

from autowsgr.application.ui.navigation.checker.backyard.canteen.checker import (
    check_canteen_page,
)


__all__ = ['check_canteen_page']
