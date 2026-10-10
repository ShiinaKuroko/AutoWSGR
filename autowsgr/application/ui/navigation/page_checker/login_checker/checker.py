"""模块功能：提供登录流程各画面的识别入口。

上层调用：
- application.ui.navigation：把登录相关画面注册为导航器的到达确认；
- application.ui.navigation.service：启动流程按顺序判断当前画面。

下层依赖：
- login_checker.recognition：提供画面事实读取与区服定位。

边界：只暴露画面判断与区服定位，不做点击、导航或启动编排。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.page_checker.login_checker import recognition


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


def check_black_screen(ctx: ContextHandle) -> bool:
    """确认是否停留在健康游戏提示画面。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        在健康游戏提示画面时为真。
    """
    return recognition.is_black_screen_visible(ctx)


def check_update_prompt(ctx: ContextHandle) -> bool:
    """确认是否出现需要更新的提示。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        出现更新提示时为真。
    """
    return recognition.is_update_prompt_visible(ctx)


def check_loading(ctx: ContextHandle) -> bool:
    """确认是否正在加载。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        显示"正在进入港区"时为真。
    """
    return recognition.is_loading_visible(ctx)


def check_login_page(ctx: ContextHandle) -> bool:
    """确认是否在登录页。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        登录页任一特征可见时为真。
    """
    return recognition.is_login_page_visible(ctx)


def check_server_select(ctx: ContextHandle) -> bool:
    """确认是否在区服选择页。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        切换大区按钮可见时为真。
    """
    return recognition.is_server_select_visible(ctx)


def find_server_position(ctx: ContextHandle, name: str) -> int | None:
    """查找目标区服在列表中的位置。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        name: 目标区服名。

    Returns:
        位置序号（0 起），未命中时返回 None。
    """
    return recognition.find_server_position(ctx, name)


def read_enter_button_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取登录页"进入游戏"按钮的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        按钮模板命中时的归一化中心；未命中时为 None。
    """
    return recognition.read_enter_button_center(ctx)


def read_switch_entry_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取登录页"点击换区"入口的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        入口模板命中时的归一化中心；未命中时为 None。
    """
    return recognition.read_switch_entry_center(ctx)


__all__ = [
    'check_black_screen',
    'check_loading',
    'check_login_page',
    'check_server_select',
    'check_update_prompt',
    'find_server_position',
    'read_enter_button_center',
    'read_switch_entry_center',
]
