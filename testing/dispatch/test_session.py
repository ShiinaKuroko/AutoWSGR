"""模块功能：验证导航会话状态的栈行为。

直接调用方：项目测试运行器。

直接依赖：pytest、dispatch.session。

边界：纯内存状态，不连接设备、不涉及导航。
"""

from __future__ import annotations

from autowsgr.dispatch.session import SessionState


def test_push_keeps_only_recent_pages() -> None:
    """压栈超过上限时丢弃最老的页面，最近一层始终可用。"""
    session = SessionState()
    for index in range(SessionState._MAX_PAGES + 5):
        session.push_page(f'页面{index}')

    assert session.current_page() == f'页面{SessionState._MAX_PAGES + 4}'
    assert len(session._pages) == SessionState._MAX_PAGES


def test_pop_and_clear() -> None:
    """弹栈返回栈顶，清栈后栈空。"""
    session = SessionState()
    session.push_page('首页')
    session.push_page('出征页面')

    assert session.pop_page() == '出征页面'
    assert session.current_page() == '首页'

    session.clear_pages()
    assert session.current_page() is None
