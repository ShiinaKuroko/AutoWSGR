"""统一处理器 — 所有请求的必经大脑 (GUI HTTP / CLI / 定时器 / 下游依赖)。

四步职责 (用户敲定):
    ① 分辨请求 (source: 谁发的, 领域: 战斗还是后勤)
    ② 理解意图 (task_type + params, 读本地 YAML 或 GUI payload)
    ③ 查当前任务 (正在跑什么, 有没有可打断)
    ④ 决策 (直接执行 / 打断让路 / 排队)

打断协作 (执行器的断点藏在 _wait 里, 见 business.base):
    interrupt() 置暂停信号并插队 → 当前执行器在最近的 _wait 断点
    回主页、抛 TaskPaused 让路 → 处理器清除信号 (明确的继续信息)、
    把被打断的任务重新入队 → 优先跑加急请求 → 跑完后被打断的任务
    从头重跑 (progress 里的计数保留)。
"""

from __future__ import annotations

import heapq
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from autowsgr.dispatch.registry import build_executor
from autowsgr.infra.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.context import GameContext


_log = get_logger('dispatch.processor')


class TaskPaused(Exception):
    """执行器在断点收到暂停, 已回主页让路 (处理器捕获后跑加急再重派)。"""


@dataclass
class Request:
    """统一请求模型 — 四类来源 (gui/cli/timer/dependency) 都包装成它。"""

    source: str = 'gui'
    """请求来源: 'gui' | 'cli' | 'timer' | 'dependency'。"""

    task_type: str = ''
    """链路名 (registry 注册名), 如 'exercise'。"""

    params: dict = field(default_factory=dict)
    """任务参数 (YAML 里 task_type 之外的字段, 如 fleet_id / times)。"""

    priority: int = 0
    """优先级, 越大越急; interrupt 会自动抬到当前任务之上。"""

    progress: dict = field(default_factory=dict)
    """任务级进度 (如 fought 计数); 暂停重跑时同一对象继续累积。"""

    @classmethod
    def from_yaml(cls, path: str | Path, *, source: str = 'cli', priority: int = 0) -> Request:
        """从计划 YAML 构造请求 — 「读本地 YAML → 确认链路」的落点。

        task_type 决定链路名, 其余字段全部作为 params 传给执行器。
        """
        import yaml

        data = yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
        task_type = data.pop('task_type', None) or data.pop('type', None)
        if not task_type:
            msg = f'YAML 缺少 task_type 字段: {path}'
            raise ValueError(msg)
        return cls(source=source, task_type=str(task_type), params=data, priority=priority)


class Processor:
    """处理器: 优先级队列 + 暂停信号 + 派发执行器。"""

    def __init__(self, ctx: GameContext, *, on_event: Callable[..., None] | None = None) -> None:
        self._ctx = ctx
        self._heap: list[tuple[int, int, Request]] = []
        self._seq = 0
        self._lock = threading.Lock()
        self._pause = threading.Event()
        self._current_priority = 0
        self.on_event = on_event
        """执行器事件回调 (event, **data); 可构造后赋值 (回调里常要引用 self)。"""

    # ── 对外 API ───────────────────────────────────────────────

    def submit(self, request: Request) -> None:
        """普通入队 (按优先级排序)。"""
        self._push(request)

    def interrupt(self, request: Request) -> None:
        """加急: 打断当前任务, 本请求抬到最高优先处理。"""
        with self._lock:
            request.priority = max(request.priority, self._current_priority + 1)
        _log.info('[Processor] 加急请求打断当前任务: {} (prio={})', request.task_type, request.priority)
        self._pause.set()
        self._push(request)

    def run_pending(self) -> list[tuple[str, Request, Any]]:
        """执行到队列清空, 返回 [(状态, 请求, 结果), ...]。

        状态: 'done' = 正常完成; 'paused' = 被打断让路 (已重新入队, 后续会重跑)。
        """
        outcomes: list[tuple[str, Request, Any]] = []
        while True:
            with self._lock:
                if not self._heap:
                    return outcomes
                request = heapq.heappop(self._heap)[2]
                self._current_priority = request.priority
            outcomes.append(self._run_one(request))

    # ── 内部 ───────────────────────────────────────────────────

    def _push(self, request: Request) -> None:
        with self._lock:
            heapq.heappush(self._heap, (-request.priority, self._seq, request))
            self._seq += 1

    def _run_one(self, request: Request) -> tuple[str, Request, Any]:
        """跑单个请求; 被打断时清信号、重排队, 让加急请求先跑。"""
        while True:
            executor = build_executor(
                request.task_type,
                self._ctx,
                request.params,
                pause=self._pause,
                progress=request.progress,
                on_event=self.on_event,
            )
            try:
                _log.info('[Processor] 执行任务: {} (source={}, prio={})',
                          request.task_type, request.source, request.priority)
                result = executor.run()
                _log.info('[Processor] 任务完成: {}', request.task_type)
                return ('done', request, result)
            except TaskPaused:
                # 执行器已回主页让路: 解除暂停 → 本任务重新入队 → 加急先跑
                _log.info('[Processor] 任务被打断, 重新排队: {} (进度保留: {})',
                          request.task_type, request.progress)
                self._pause.clear()
                self._push(request)
                return ('paused', request, None)
