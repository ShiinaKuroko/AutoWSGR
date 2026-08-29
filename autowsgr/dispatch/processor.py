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
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import yaml

from autowsgr.dispatch.registry import build_executor
from autowsgr.infra.file_utils import load_yaml
from autowsgr.infra.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.context import GameContext


_log = get_logger('dispatch.processor')


class TaskPaused(Exception):  # noqa: N818 - public protocol name
    """执行器在断点收到暂停, 已回主页让路 (处理器捕获后跑加急再重派)。"""


class TaskStopped(Exception):  # noqa: N818 - public protocol name
    """执行器收到协作式停止请求, 已回主页并结束当前任务。"""


# 数字越大越优先。外部入口不接受任意优先级, 统一从任务类型推导。
# 业务优先级保持在约定的 0-10 范围内, 0 留给未分类任务。
MAX_PRIORITY = 10
TASK_PRIORITIES: dict[str, int] = {
    'expedition_check': 6,
    'reward_check': 5,
    'campaign': 4,
    'exercise': 3,
    'decisive': 2,
    'normal_fight': 1,
    'event_fight': 1,
}


def priority_for(task_type: str) -> int:
    """返回任务类型的调度优先级, 未知业务按最低优先级处理。"""
    return TASK_PRIORITIES.get(task_type, 0)


def _validate_exercise_params(params: Mapping[str, Any]) -> None:
    """校验演习 YAML 的业务字段, 不把错误推迟到设备操作阶段。"""
    allowed = {'fleet_id', 'rival', 'rivals_limit'}
    unknown = sorted(set(params) - allowed)
    if unknown:
        raise ValueError(f'演习 YAML 包含未知字段: {", ".join(unknown)}')

    for name in ('fleet_id', 'rival', 'rivals_limit'):
        value = params.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f'演习字段 {name} 必须是正整数')
    if params.get('fleet_id', 1) > 6:
        raise ValueError('演习字段 fleet_id 必须在 1-6 范围内')
    if params.get('rival') is not None and params['rival'] > 5:
        raise ValueError('演习字段 rival 必须在 1-5 范围内')


def _validate_params(task_type: str, params: Mapping[str, Any]) -> None:
    """运行当前已迁移链路的字段校验; 其他链路保留其既有校验器。"""
    if task_type == 'exercise':
        _validate_exercise_params(params)


@dataclass(frozen=True, slots=True)
class Request:
    """统一请求模型 — 四类来源 (gui/cli/timer/dependency) 都包装成它。"""

    source: str = 'gui'
    """请求来源: 'gui' | 'cli' | 'timer' | 'dependency'。"""

    task_type: str = ''
    """链路名 (registry 注册名), 如 'exercise'。"""

    params: Mapping[str, Any] = field(default_factory=dict)
    """任务参数快照 (不允许执行器在运行中改写)。"""

    priority: int | None = None
    """优先级, 越大越急; interrupt 会自动抬到当前任务之上。"""

    count: int = 1
    """同一请求提交的有限执行次数, 与 YAML 业务字段分离。"""

    extre: bool = False
    """是否为外部插队意图; 仅影响处理器排队, 不传入业务参数。"""

    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    """请求幂等标识, 供入口层去重和状态追踪。"""

    progress: dict[str, Any] = field(default_factory=dict, compare=False)
    """任务级进度 (如 fought 计数); 暂停重跑时同一对象继续累积。"""

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError('source 必须是非空字符串')
        if not isinstance(self.task_type, str) or not self.task_type.strip():
            raise ValueError('task_type 不能为空')
        object.__setattr__(self, 'source', self.source.strip())
        object.__setattr__(self, 'task_type', self.task_type.strip())
        if isinstance(self.count, bool) or not isinstance(self.count, int) or self.count < 1:
            raise ValueError('count 必须是正整数')
        if not isinstance(self.extre, bool):
            raise ValueError('extre 必须是布尔值')  # noqa: TRY004 - admission errors share ValueError
        if self.priority is not None and (
            isinstance(self.priority, bool)
            or not isinstance(self.priority, int)
            or not 0 <= self.priority <= MAX_PRIORITY
        ):
            raise ValueError(f'priority 必须是 0-{MAX_PRIORITY} 的整数')
        if self.params is None:
            params = {}
        elif isinstance(self.params, Mapping):
            params = dict(self.params)
        else:
            raise ValueError('params 必须是映射')
        _validate_params(self.task_type, params)
        object.__setattr__(self, 'params', MappingProxyType(params))
        if self.priority is None:
            object.__setattr__(self, 'priority', priority_for(self.task_type))
        elif self.priority < 0:
            raise ValueError('priority 不能为负数')

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        *,
        source: str = 'cli',
        count: int = 1,
        extre: bool = False,
        priority: int | None = None,
    ) -> Request:
        """从计划 YAML 构造请求 — 「读本地 YAML → 确认链路」的落点。

        task_type 决定链路名, 其余字段作为不可变 params 快照传给执行器。
        旧计划中的 ``times: 1`` 只作为兼容字段丢弃; 大于 1 时明确要求
        调用方改用入口的 ``count`` 参数, 避免把两种次数语义混在 YAML 中。
        """
        resolved = Path(path).expanduser().resolve()
        if resolved.suffix.lower() not in {'.yaml', '.yml'}:
            raise ValueError(f'任务文件必须是 YAML: {resolved}')
        if not resolved.is_file():
            raise FileNotFoundError(f'任务文件不存在: {resolved}')
        try:
            data = load_yaml(resolved)
        except yaml.YAMLError as exc:
            raise ValueError(f'任务 YAML 解析失败: {resolved}') from exc
        if not isinstance(data, dict):
            raise ValueError(  # noqa: TRY004 - HTTP maps all YAML admission errors to 422
                f'任务 YAML 顶层必须是对象: {resolved}',
            )
        raw_type = data.get('task_type')
        legacy_type = data.get('type')
        if raw_type is not None and legacy_type is not None and raw_type != legacy_type:
            raise ValueError('YAML 的 task_type 与 type 不一致')
        task_type = raw_type or legacy_type
        if not task_type:
            msg = f'YAML 缺少 task_type 字段: {resolved}'
            raise ValueError(msg)
        if not isinstance(task_type, str):
            raise ValueError('YAML 的 task_type 必须是字符串')  # noqa: TRY004
        params = {key: value for key, value in data.items() if key not in {'task_type', 'type'}}
        legacy_count = params.pop('times', None)
        if legacy_count is not None and legacy_count != 1:
            raise ValueError('YAML 的 times 已废弃, 请通过入口 count 参数提交次数')
        return cls(
            source=source,
            task_type=task_type,
            params=params,
            count=count,
            extre=extre,
            priority=priority,
        )


class Processor:
    """处理器: 优先级队列 + 暂停信号 + 派发执行器。"""

    def __init__(
        self,
        ctx: GameContext,
        *,
        on_event: Callable[..., None] | None = None,
        stop: threading.Event | None = None,
        recover: Callable[[], None] | None = None,
        soft_retries: int = 1,
        hard_retries: int = 1,
    ) -> None:
        self._ctx = ctx
        self._heap: list[tuple[int, int, int, Request]] = []
        self._seq = 0
        self._lock = threading.Lock()
        self._run_lock = threading.Lock()
        self._pause = threading.Event()
        self._stop = stop if stop is not None else threading.Event()
        self._current_priority = 0
        self._current_request: Request | None = None
        self._recover = recover or self._default_recover
        self._soft_retries = max(0, soft_retries)
        self._hard_retries = max(0, hard_retries)
        self.on_event = on_event
        """执行器事件回调 (event, **data); 可构造后赋值 (回调里常要引用 self)。"""

    # ── 对外 API ───────────────────────────────────────────────

    def submit(self, request: Request) -> str:
        """普通入队 (按优先级排序)。"""
        self._push(request)
        return request.request_id

    def interrupt(self, request: Request) -> None:
        """加急: 打断当前任务, 本请求抬到最高优先处理。"""
        with self._lock:
            priority = min(MAX_PRIORITY, max(request.priority or 0, self._current_priority + 1))
            request = replace(request, priority=priority, extre=True)
            should_pause = self._current_request is not None
        _log.info('[Processor] 加急请求打断当前任务: {} (prio={})', request.task_type, priority)
        if should_pause:
            self._pause.set()
        self._push(request)

    def stop(self) -> None:
        """请求当前执行器在最近安全断点停止并回主页。"""
        self._stop.set()
        self._pause.set()

    @property
    def is_running(self) -> bool:
        """当前是否正在执行一个请求。"""
        return self._current_request is not None

    def run_pending(self) -> list[tuple[str, Request, Any]]:
        """执行到队列清空, 返回 [(状态, 请求, 结果), ...]。

        状态: 'done' = 正常完成; 'paused' = 被打断让路 (已重新入队, 后续会重跑)。
        """
        with self._run_lock:
            outcomes: list[tuple[str, Request, Any]] = []
            while True:
                with self._lock:
                    if not self._heap:
                        self._current_priority = 0
                        return outcomes
                    request = heapq.heappop(self._heap)[3]
                    self._current_priority = request.priority or 0
                    self._current_request = request
                try:
                    outcomes.extend(self._run_request(request))
                finally:
                    with self._lock:
                        self._current_request = None

    # ── 内部 ───────────────────────────────────────────────────

    def _push(self, request: Request) -> None:
        with self._lock:
            # The explicit insertion flag breaks a max-priority tie without
            # widening the public 0-10 priority contract.
            heapq.heappush(
                self._heap,
                (-(request.priority or 0), 0 if request.extre else 1, self._seq, request),
            )
            self._seq += 1

    def _run_request(self, request: Request) -> list[tuple[str, Request, Any]]:
        """执行请求的剩余次数; 每次完成都产出一个可观察结果。"""
        outcomes: list[tuple[str, Request, Any]] = []
        raw_completed = request.progress.get('_completed', 0)
        if (
            isinstance(raw_completed, bool)
            or not isinstance(raw_completed, int)
            or raw_completed < 0
        ):
            raise ValueError('任务进度 _completed 必须是非负整数')
        if raw_completed > request.count:
            raise ValueError('任务进度 _completed 不能超过 count')
        completed = raw_completed
        while completed < request.count:
            if self._stop.is_set():
                outcomes.append(('stopped', request, None))
                return outcomes
            status, result = self._run_one(request)
            if status == 'paused':
                self._push(request)
                outcomes.append(('paused', request, None))
                return outcomes
            if status == 'stopped':
                outcomes.append(('stopped', request, None))
                return outcomes
            if status == 'failed':
                outcomes.append(('failed', request, result))
                return outcomes
            completed += 1
            request.progress['_completed'] = completed
            self._report('completed', count=completed, total=request.count)
            outcomes.append(('done', request, result))
        return outcomes

    def _run_one(self, request: Request) -> tuple[str, Any]:  # noqa: PLR0911 - state machine exits
        """执行一次业务, 处理暂停、停止及软/硬重试。"""
        soft_attempts = 0
        hard_attempts = 0
        while True:
            if self._stop.is_set():
                return 'stopped', None
            executor = build_executor(
                request.task_type,
                self._ctx,
                request.params,
                pause=self._pause,
                stop=self._stop,
                progress=request.progress,
                on_event=self.on_event,
            )
            try:
                _log.info(
                    '[Processor] 执行任务: {} (source={}, prio={})',
                    request.task_type,
                    request.source,
                    request.priority,
                )
                result = executor.run()
            except TaskPaused:
                _log.info('[Processor] 任务被打断, 保留进度: {}', request.progress)
                self._pause.clear()
                return 'paused', None
            except TaskStopped:
                _log.info('[Processor] 任务已停止: {}', request.task_type)
                self._pause.clear()
                return 'stopped', None
            except Exception as exc:
                if self._stop.is_set():
                    return 'stopped', None
                if soft_attempts < self._soft_retries:
                    soft_attempts += 1
                    self._report('retry', mode='soft', attempt=soft_attempts, error=str(exc))
                    continue
                if hard_attempts < self._hard_retries:
                    hard_attempts += 1
                    self._report('retry', mode='hard', attempt=hard_attempts, error=str(exc))
                    try:
                        self._recover()
                    except Exception as recovery_error:
                        return 'failed', f'硬重试初始化失败: {recovery_error}'
                    soft_attempts = 0
                    continue
                _log.error('[Processor] 任务失败: {} - {}', request.task_type, exc)
                return 'failed', str(exc)
            else:
                _log.info('[Processor] 任务完成: {}', request.task_type)
                return 'done', result

    def _default_recover(self) -> None:
        """硬重试的唯一恢复动作: 重新初始化到主页。"""
        from autowsgr.business.system.initialize.initialize import initialize

        initialize(self._ctx)

    def _report(self, event: str, **data: Any) -> None:
        if self.on_event is not None:
            self.on_event(event, **data)
