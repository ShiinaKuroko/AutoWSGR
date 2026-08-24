"""执行器基类 — 处理器驱动模型下的被动域专家。

架构位置 (用户敲定的调度模型):

    请求 (GUI/CLI/定时器) → 处理器 (dispatch.processor: 分辨/排队/打断决策)
        → 执行器 (本基类的子类: 判断任务怎么执行)
            → 导航器 (goto_page, 移动外包) + 域内业务操作 → 回主页上报

暂停协议 (断点免费藏在等待里):
    处理器置位 pause 信号 → 执行器在最近的 ``_wait()`` 发现 →
    回主页 (锚点铁律) → 上报 ``paused`` → 抛 :class:`TaskPaused` 让出执行权。
    处理器跑完加急请求后清除信号并重新派发 → 执行器**从头重跑** (幂等,
    游戏状态实时识别所以重跑天然安全), 任务级进度 (``self.progress``) 保留。

子类约定:
    - 实现 ``_execute()``, 用 ``self._wait()`` 代替 ``time.sleep``,
      断点自动获得; 战斗等原子段内部用 ``time.sleep`` (禁止查暂停)。
    - 用 ``self._report(event, **data)`` 上报业务事件 (计数/进度)。
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any

from autowsgr.business.system.navigate import goto_page
from autowsgr.dispatch.processor import TaskPaused
from autowsgr.types import PageName


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.context import GameContext


class BaseExecutor:
    """执行器基类: 等待收口 + 暂停断点 + 事件上报。"""

    def __init__(
        self,
        ctx: GameContext,
        params: dict | None = None,
        *,
        pause: threading.Event | None = None,
        progress: dict | None = None,
        on_event: Callable[[str, ...], None] | None = None,
    ) -> None:
        self.ctx = ctx
        self.params = dict(params or {})
        self.progress = progress if progress is not None else {}
        """任务级进度 (如 fought 计数), 暂停重跑后由处理器传入同一 dict 保留。"""
        self._pause = pause if pause is not None else threading.Event()
        self._on_event = on_event

    def run(self) -> Any:
        """任务入口 (单趟): 正常返回结果; 断点收到暂停时抛 TaskPaused。

        重跑循环归处理器管 (它要先跑加急请求再重新派发本任务)。
        """
        return self._execute()

    def _execute(self) -> Any:
        """子类实现: 任务的完整执行过程。"""
        raise NotImplementedError

    def _wait(self, seconds: float) -> None:
        """唯一等待出口 = 免费断点: 等待前查暂停, 收到则回主页让路。"""
        self._check_pause()
        time.sleep(seconds)

    def _check_pause(self) -> None:
        """断点检查: 处理器发了暂停 → 回主页 → 上报 → 让出执行权。"""
        if not self._pause.is_set():
            return
        goto_page(self.ctx, PageName.MAIN)
        self._report('paused')
        raise TaskPaused

    def _report(self, event: str, **data: Any) -> None:
        """上报业务事件 (panel_ready / rival_done / paused ...), 处理器转发。"""
        if self._on_event is not None:
            self._on_event(event, **data)
