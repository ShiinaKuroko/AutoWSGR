"""游戏更新处理 — 独立模块 (空实现占位)。

背景:
    启动流程中, 游戏可能停在更新界面 (下载进度条 / 安装确认),
    当前没有更新界面的截图样本, 无法做识别。

预留接口 (未来填充):
    needs_update(screen) — 识别更新界面特征 (模板匹配)
    handle(ctrl)         — 等待下载完成 → 点安装 → 等游戏重启

initialize 启动流程中的调用点::

    if updater.needs_update(screen):
        updater.handle(ctrl)   # 未来: 处理完更新后继续登录流程
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.emulator import AndroidController


def needs_update(screen: np.ndarray) -> bool:
    """检测当前画面是否为游戏更新界面。

    空实现: 永远返回 ``False``, 不改变现有启动行为。
    """
    return False


def handle(ctrl: AndroidController) -> None:
    """处理游戏更新流程 (等待下载 / 点击安装 / 重启游戏)。

    空实现: 不做任何动作。
    """
    return None
