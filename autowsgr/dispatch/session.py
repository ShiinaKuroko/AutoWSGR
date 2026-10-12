"""模块功能：维护程序运行期内的会话状态。

上层调用：
- application.ui.navigation.service：记录导航栈与区服选择标记。
- application.ui.navigation.checker 与 registry：读写每日浮窗的处理标记。

下层依赖：无，只保存进程内状态。

边界：只保存程序运行期内的状态，重启即消失；不保存任务级事实、不访问设备、不做业务判断。
"""

from __future__ import annotations


class SessionState:
    """程序运行期内的导航会话状态。"""

    # 只保留最近若干层页面：更老的历史既不影响算路（只看栈顶），也回退不到，
    # 留着只会随运行时间无限增长。
    _MAX_PAGES = 8

    def __init__(self) -> None:
        self._server_selected = False
        self._news_handled = False
        self._reward_handled = False
        self._pages: list[str] = []

    @property
    def server_selected(self) -> bool:
        """本次程序运行是否已处理过区服选择。"""
        return self._server_selected

    def mark_server_selected(self) -> None:
        """标记本次运行已完成区服选择。"""
        self._server_selected = True

    @property
    def news_handled(self) -> bool:
        """本次运行是否已处理过每日公告浮窗。"""
        return self._news_handled

    def mark_news_handled(self) -> None:
        """标记每日公告浮窗已处理干净；处理失败时不调用。"""
        self._news_handled = True

    @property
    def reward_handled(self) -> bool:
        """本次运行是否已处理过每日奖励浮窗与它的确认浮窗。"""
        return self._reward_handled

    def mark_reward_handled(self) -> None:
        """标记每日奖励浮窗已处理干净；处理失败时不调用。"""
        self._reward_handled = True

    def current_page(self) -> str | None:
        """返回导航栈顶的页面值。"""
        return self._pages[-1] if self._pages else None

    def push_page(self, page: str) -> None:
        """把页面压入导航栈，只保留最近若干层。"""
        self._pages.append(page)
        del self._pages[: -self._MAX_PAGES]

    def pop_page(self) -> str | None:
        """弹出导航栈顶的页面值。"""
        return self._pages.pop() if self._pages else None

    def clear_pages(self) -> None:
        """清空导航栈；游戏被强杀重开后栈里的页面已经不存在。"""
        self._pages.clear()


_SESSION = SessionState()


def get_session() -> SessionState:
    """返回进程级会话状态。"""
    return _SESSION


__all__ = ['SessionState', 'get_session']
