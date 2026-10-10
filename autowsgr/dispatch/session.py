"""模块功能：维护程序运行期内的会话状态。

上层调用：
- application.ui.navigation.service：记录导航栈与每日弹窗处理标记。

下层依赖：无，只保存进程内状态。

边界：只保存程序运行期内的状态，重启即消失；不保存任务级事实、不访问设备、不做业务判断。
"""

from __future__ import annotations


class SessionState:
    """程序运行期内的导航会话状态。"""

    def __init__(self) -> None:
        self._daily_popup_handled = False
        self._pages: list[str] = []

    @property
    def daily_popup_handled(self) -> bool:
        """本次程序运行是否已处理过每日弹窗。"""
        return self._daily_popup_handled

    def mark_daily_popup_handled(self) -> None:
        """标记每日弹窗已处理。"""
        self._daily_popup_handled = True

    def current_page(self) -> str | None:
        """返回导航栈顶的页面值。"""
        return self._pages[-1] if self._pages else None

    def push_page(self, page: str) -> None:
        """把页面压入导航栈。"""
        self._pages.append(page)

    def pop_page(self) -> str | None:
        """弹出导航栈顶的页面值。"""
        return self._pages.pop() if self._pages else None


_SESSION = SessionState()


def get_session() -> SessionState:
    """返回进程级会话状态。"""
    return _SESSION


__all__ = ['SessionState', 'get_session']
