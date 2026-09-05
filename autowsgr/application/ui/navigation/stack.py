"""记录页面来路，并为导航中的下一次识别提供候选页面。

`service._goto_page` 调用 `observe`、`push` 和 `candidates`；识别失败时由
`recognition` 调用 `reset` 或 `clear`。本文件只依赖导航图的邻接关系和页面名类型，
不读取截图、不调用设备。
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.graph import neighbors
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.types import PageName


_log = get_logger('ui')

OVERLAY_CANDIDATES: set[str] = set()
"""任意导航步都可能出现的覆盖型页面。"""


@dataclass(slots=True)
class _StackFrame:
    """页面栈中的一帧。"""

    page: str
    screen: np.ndarray | None = None


class UIStack:
    """记录页面来路、识别对账和下一步识别候选。"""

    def __init__(self, *, max_depth: int = 8, keep_frames: int = 2) -> None:
        """创建空页面栈。"""
        self._frames: list[_StackFrame] = []
        self._max_depth = max_depth
        self._keep_frames = keep_frames
        self._drifted = False
        self._lock = threading.Lock()

    # -- 栈能力 ------------

    def candidates(self, target: str | PageName | None = None) -> set[str]:
        """生成下一次页面识别的候选集合。"""
        # 1、保留当前页和相邻页，覆盖正常前进。
        with self._lock:
            current = self._frames[-1].page if self._frames else None
            parent = self._frames[-2].page if len(self._frames) >= 2 else None

        result: set[str] = set()
        if current is not None:
            result.add(current)
            result |= neighbors(current)
        # 2、保留父页和目标页，覆盖回退与无入边页面。
        if parent is not None:
            result.add(parent)
        if target is not None:
            name = _page_name(target)
            result.add(name)
            result |= neighbors(name)
        # 3、保留全局覆盖页，避免弹窗把识别范围挡住。
        result |= OVERLAY_CANDIDATES
        return result

    def clear(self) -> None:
        """清空页面栈并重置漂移标记。"""
        with self._lock:
            self._frames.clear()
            self._drifted = False

    @property
    def current(self) -> str | None:
        """返回当前页面。"""
        with self._lock:
            return self._frames[-1].page if self._frames else None

    @property
    def depth(self) -> int:
        """返回当前栈深。"""
        with self._lock:
            return len(self._frames)

    @property
    def drifted(self) -> bool:
        """返回页面是否脱离栈预测。"""
        return self._drifted

    def observe(self, identified: str | PageName, *, screen: np.ndarray | None = None) -> str:
        """用识别结果校正页面栈。"""
        # 1、先把识别结果转成统一页面名。
        name = _page_name(identified)
        with self._lock:
            if not self._frames:
                self._frames = [_StackFrame(name, screen)]
                return name

            current = self._frames[-1].page
            parent = self._frames[-2].page if len(self._frames) >= 2 else None
            if name == current:
                self._frames[-1].screen = screen
                return current
            if parent is not None and name == parent:
                self._frames.pop()
                self._frames[-1].screen = screen
                return name
            if name in neighbors(current):
                self._frames.append(_StackFrame(name, screen))
                self._trim()
                return name

            # 2、无法对应当前路径时保留栈，标记为漂移。
            self._drifted = True
            _log.warning(
                "[UIStack] 漂移: 识别为 '{}', 栈预测 '{}' (栈: {})",
                name,
                current,
                ' → '.join(frame.page for frame in self._frames),
            )
            return current

    def pages(self) -> tuple[str, ...]:
        """返回页面栈快照。"""
        with self._lock:
            return tuple(frame.page for frame in self._frames)

    @property
    def parent(self) -> str | None:
        """返回当前页面的父页面。"""
        with self._lock:
            return self._frames[-2].page if len(self._frames) >= 2 else None

    def pop(self) -> str | None:
        """弹出并返回当前页面。"""
        with self._lock:
            if not self._frames:
                return None
            return self._frames.pop().page

    def push(self, page: str | PageName, *, screen: np.ndarray | None = None) -> None:
        """声明进入新页面。"""
        name = _page_name(page)
        with self._lock:
            if self._frames and self._frames[-1].page == name:
                self._frames[-1].screen = screen
            else:
                self._frames.append(_StackFrame(name, screen))
            self._trim()

    def replace(self, page: str | PageName, *, screen: np.ndarray | None = None) -> None:
        """替换栈顶页面。"""
        name = _page_name(page)
        with self._lock:
            self._frames[-1:] = [_StackFrame(name, screen)]
            self._drifted = False
            self._trim()

    def reset(self, page: str | PageName, *, screen: np.ndarray | None = None) -> None:
        """清空页面栈并以页面作为新根。"""
        name = _page_name(page)
        with self._lock:
            self._frames = [_StackFrame(name, screen)]
            self._drifted = False

    def snapshot(self, page: str | PageName) -> np.ndarray | None:
        """返回页面留存的最近截图。"""
        name = _page_name(page)
        with self._lock:
            for frame in reversed(self._frames):
                if frame.page == name:
                    return frame.screen
        return None

    # -- 内部辅助 ------------

    def _trim(self) -> None:
        """限制栈深和截图留存数量。"""
        if len(self._frames) > self._max_depth:
            del self._frames[: len(self._frames) - self._max_depth]
        for index, frame in enumerate(self._frames):
            if len(self._frames) - index > self._keep_frames:
                frame.screen = None


def _page_name(page: str | PageName) -> str:
    """把页面名归一为字符串。"""
    return page.value if hasattr(page, 'value') else page


__all__ = ['UIStack']
