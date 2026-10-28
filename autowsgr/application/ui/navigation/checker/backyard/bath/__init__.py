"""模块功能：提供浴室二级页检查器的模块入口。

上层调用：
- application.ui.navigation：调用浴室二级页的确认入口。

下层依赖：
- bath.checker：提供识别入口。

本模块只导出稳定入口，不放业务实现。
"""

from autowsgr.application.ui.navigation.checker.backyard.bath.checker import (
    check_bath_page,
)


__all__ = ['check_bath_page']
