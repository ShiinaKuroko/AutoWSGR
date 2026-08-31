"""任务执行路由 — /api/task/*"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException
from pydantic import Discriminator

from autowsgr.common.system.logger import get_logger
from autowsgr.dispatch.processor import Processor, Request
from autowsgr.server.device_lease import DeviceOperationBusyError
from autowsgr.server.schemas import (
    ApiResponse,
    CampaignRequest,
    DecisiveRequest,
    EventFightRequest,
    ExerciseRequest,
    NormalFightRequest,
    TaskStatusResponse,
    YamlTaskRequest,
)
from autowsgr.server.serializers import (
    apply_combat_plan_overrides,
    build_combat_plan,
    build_fleet_selection,
    convert_combat_result,
)
from autowsgr.server.task_manager import TaskOutcome, task_manager

from ..main import get_context, lifecycle_lock
from . import require_context


_log = get_logger('server')

router = APIRouter(prefix='/api/task', tags=['task'])


TaskRequestUnion = Annotated[
    NormalFightRequest
    | EventFightRequest
    | CampaignRequest
    | ExerciseRequest
    | DecisiveRequest
    | YamlTaskRequest,
    Discriminator('type'),
]


def _start_task(
    task_type: str,
    total_rounds: int,
    executor: Any,
) -> ApiResponse:
    task_id = task_manager.start_task(
        task_type=task_type,
        total_rounds=total_rounds,
        executor=executor,
    )
    return ApiResponse(
        success=True,
        data={'task_id': task_id, 'status': 'running'},
        message='任务已启动',
    )


@router.post('/start', response_model=ApiResponse)
async def task_start(request: TaskRequestUnion) -> ApiResponse:  # type: ignore[arg-type]  # noqa: PLR0911
    """启动任务 (异步执行，立即返回)。"""
    async with lifecycle_lock:
        if task_manager.is_running:
            return await _handle_running_task(request)

        ctx = require_context(get_context)

        ctx.stop_event = task_manager.stop_event

        try:
            if isinstance(request, YamlTaskRequest):
                try:
                    return await _start_yaml_task(ctx, request)
                except (FileNotFoundError, ValueError) as error:
                    raise HTTPException(status_code=422, detail=str(error)) from error
            if isinstance(request, NormalFightRequest):
                return await _start_normal_fight(ctx, request)
            elif isinstance(request, EventFightRequest):
                return await _start_event_fight(ctx, request)
            elif isinstance(request, CampaignRequest):
                try:
                    return await _start_campaign(ctx, request)
                except ValueError as error:
                    raise HTTPException(status_code=422, detail=str(error)) from error
            elif isinstance(request, ExerciseRequest):
                return await _start_exercise(ctx, request)
            elif isinstance(request, DecisiveRequest):
                return await _start_decisive(ctx, request)
            else:
                raise HTTPException(status_code=400, detail='未知的任务类型')
        except DeviceOperationBusyError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error


async def _handle_running_task(request: TaskRequestUnion) -> ApiResponse:
    """把允许的 YAML 插队请求转给当前 Processor。"""
    if not isinstance(request, YamlTaskRequest) or not request.extre:
        raise HTTPException(status_code=409, detail='已有任务正在运行')

    require_context(get_context)
    try:
        queued = Request.from_yaml(
            request.yaml_path,
            source='gui',
            count=request.count,
            extre=True,
            ship_name_aliases=request.ship_name_aliases,
        )
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if not task_manager.interrupt_processor(queued):
        raise HTTPException(status_code=409, detail='当前任务尚未绑定处理器')
    return ApiResponse(
        success=True,
        data={'task_id': queued.request_id, 'status': 'queued'},
        message='插队任务已受理',
    )


@router.post('/start-yaml', response_model=ApiResponse)
async def task_start_yaml(request: YamlTaskRequest) -> ApiResponse:
    """按 YAML 路径启动一次或多次任务。"""
    return await task_start(request)


@router.post('/stop', response_model=ApiResponse)
async def task_stop() -> ApiResponse:
    """停止当前任务。"""
    if not task_manager.stop_task():
        return ApiResponse(success=True, message='没有正在运行的任务')

    return ApiResponse(
        success=True,
        data={
            'task_id': task_manager.current_task.task_id,
            'status': 'stopped',
        },
        message='已请求停止任务',
    )


@router.get(
    '/status',
    response_model=ApiResponse[TaskStatusResponse],
    response_model_exclude_unset=True,
)
async def task_status() -> ApiResponse[TaskStatusResponse]:
    """查询当前任务状态。"""
    status = task_manager.get_status()
    return ApiResponse[TaskStatusResponse](success=True, data=status)


async def _start_yaml_task(ctx: Any, request: YamlTaskRequest) -> ApiResponse:
    """把文件请求转换为 Processor 请求, 再交给现有后台生命周期适配器。"""
    task_request = Request.from_yaml(
        request.yaml_path,
        source='gui',
        count=request.count,
        extre=request.extre,
        ship_name_aliases=request.ship_name_aliases,
    )

    return _start_task(
        task_request.task_type,
        task_request.count,
        lambda _task_info: _run_processor_request(ctx, task_request),
    )


def _run_processor_request(ctx: Any, request: Request) -> TaskOutcome:  # noqa: PLR0912
    """执行一份 Processor 请求并转换成现有 HTTP 结果封装。"""

    def on_event(event: str, **data: Any) -> None:
        if event == 'completed' and data.get('task_type', request.task_type) == request.task_type:
            task_manager.update_progress(
                current_round=int(data.get('count', 0)),
                current_node=request.task_type,
            )

    processor = Processor(ctx, stop=task_manager.stop_event, on_event=on_event)
    attach_processor = getattr(task_manager, 'attach_processor', None)
    detach_processor = getattr(task_manager, 'detach_processor', None)
    if attach_processor is not None:
        attach_processor(processor)
    try:
        if request.extre:
            processor.interrupt(request)
        else:
            processor.submit(request)
        outcomes = processor.run_pending()
    finally:
        if detach_processor is not None:
            detach_processor(processor)
    details: list[dict[str, Any]] = []
    completed = 0
    error: str | None = None
    for status, _request, raw in outcomes:
        if status == 'done':
            if _request.task_type != request.task_type:
                continue
            completed += 1
            converted = _processor_details(
                raw,
                len(details) + 1,
                include_flag=request.task_type == 'campaign',
            )
            if not converted and request.task_type == 'exercise':
                converted = [
                    {
                        'round': len(details) + 1,
                        'success': True,
                        'result': 'skip fight',
                    },
                ]
            details.extend(converted)
        elif status == 'failed':
            if _request.task_type != request.task_type:
                _log.error('[Task] 插队任务 {} 失败: {}', _request.task_type, raw)
                continue
            error = str(raw)
            details.append({'round': len(details) + 1, 'success': False, 'error': error})
            break
        elif status == 'stopped':
            break
    for detail in details:
        task_manager.add_result(detail)
    task_manager.update_progress(current_round=completed, current_node=request.task_type)
    return TaskOutcome.from_results(details, error=error)


def _processor_details(
    raw: Any,
    first_round: int,
    *,
    include_flag: bool = False,
) -> list[dict[str, Any]]:
    """将一次 Processor 结果转换成 GUI 需要的扁平轮次记录。"""
    from autowsgr.business.combat import CombatResult

    if isinstance(raw, list):
        details: list[dict[str, Any]] = []
        for index, item in enumerate(raw, 1):
            if isinstance(item, CombatResult):
                detail = convert_combat_result(item, first_round + index - 1)
                if include_flag:
                    detail['result'] = item.flag.value
                details.append(detail)
            elif isinstance(item, dict):
                detail = dict(item)
                detail.setdefault('round', first_round + index - 1)
                detail.setdefault('success', True)
                details.append(detail)
            else:
                details.append(
                    {'round': first_round + index - 1, 'success': True, 'result': item},
                )
        return details
    if isinstance(raw, CombatResult):
        detail = convert_combat_result(raw, first_round)
        if include_flag:
            detail['result'] = raw.flag.value
        return [detail]
    if isinstance(raw, dict):
        detail = dict(raw)
        detail.setdefault('round', first_round)
        detail.setdefault('success', True)
        return [detail]
    return [{'round': first_round, 'success': True, 'result': raw}]


# ═══════════════════════════════════════════════════════════════════════════════
# 任务启动辅助
# ═══════════════════════════════════════════════════════════════════════════════


async def _start_normal_fight(ctx: Any, request: NormalFightRequest) -> ApiResponse:
    """启动常规战任务。"""
    from autowsgr.business.combat import CombatPlan
    from autowsgr.ops import run_normal_fight

    def executor(_task_info: Any) -> TaskOutcome:
        results = []

        if request.plan_id:
            plan = CombatPlan.from_yaml(request.plan_id)
            apply_combat_plan_overrides(plan, request.plan)
        elif request.plan:
            plan = build_combat_plan(request.plan)
        else:
            raise ValueError('必须提供 plan 或 plan_id')

        # API plan 覆盖 YAML 节点配置和舰队；DTO 在 runner 启动前转换成领域模型。
        fleet_selection = build_fleet_selection(plan, request.plan)

        for i in range(request.times):
            if task_manager.should_stop():
                break

            task_manager.update_progress(current_round=i + 1)
            _log.info('[Task] 常规战第 {}/{} 轮', i + 1, request.times)

            try:
                result = run_normal_fight(
                    ctx,
                    plan,
                    times=1,
                    fleet_selection=fleet_selection,
                )[0]
                results.append(convert_combat_result(result, i + 1))
                task_manager.add_result(results[-1])
            except Exception as e:
                _log.error('[Task] 第 {} 轮失败: {}', i + 1, e)
                results.append({'round': i + 1, 'success': False, 'error': str(e)})

        return TaskOutcome.from_results(results)

    return _start_task('normal_fight', request.times, executor)


async def _start_event_fight(ctx: Any, request: EventFightRequest) -> ApiResponse:
    """启动活动战任务。"""
    from autowsgr.business.combat import CombatPlan
    from autowsgr.ops import run_event_fight

    def executor(_task_info: Any) -> TaskOutcome:
        results = []

        if request.plan_id:
            plan = CombatPlan.from_yaml(request.plan_id)
            apply_combat_plan_overrides(plan, request.plan)
        elif request.plan:
            plan = build_combat_plan(request.plan)
        else:
            raise ValueError('必须提供 plan 或 plan_id')

        # 活动战顶层 fleet_id 优先，其余覆盖规则与普通战完全一致。
        fleet_selection = build_fleet_selection(
            plan,
            request.plan,
            fleet_id=request.fleet_id,
        )

        for i in range(request.times):
            if task_manager.should_stop():
                break

            task_manager.update_progress(current_round=i + 1)
            _log.info('[Task] 活动战第 {}/{} 轮', i + 1, request.times)

            try:
                result = run_event_fight(
                    ctx,
                    plan,
                    times=1,
                    fleet_selection=fleet_selection,
                )[0]
                results.append(convert_combat_result(result, i + 1))
                task_manager.add_result(results[-1])
            except Exception as e:
                _log.error('[Task] 第 {} 轮失败: {}', i + 1, e)
                results.append({'round': i + 1, 'success': False, 'error': str(e)})

        return TaskOutcome.from_results(results)

    return _start_task('event_fight', request.times, executor)


async def _start_campaign(ctx: Any, request: CampaignRequest) -> ApiResponse:
    """把战役请求交给 Processor 执行。"""
    task_request = Request(
        source='gui',
        task_type='campaign',
        params={'campaign_name': request.campaign_name},
        count=request.times,
    )
    return _start_task(
        task_request.task_type,
        task_request.count,
        lambda _task_info: _run_processor_request(ctx, task_request),
    )


async def _start_exercise(ctx: Any, request: ExerciseRequest) -> ApiResponse:
    """启动演习任务。"""
    task_request = Request(
        source='gui',
        task_type='exercise',
        params={'fleet_id': request.fleet_id},
    )
    return _start_task(
        task_request.task_type,
        task_request.count,
        lambda _task_info: _run_processor_request(ctx, task_request),
    )


async def _start_decisive(ctx: Any, request: DecisiveRequest) -> ApiResponse:
    """启动决战任务。"""
    from autowsgr.common.system import DecisiveConfig
    from autowsgr.ops import DecisiveController

    def executor(_task_info: Any) -> TaskOutcome:
        config = DecisiveConfig(
            chapter=request.chapter,
            decisive_rounds=request.decisive_rounds,
            use_new_fleet_change_algorithm=request.use_new_fleet_change_algorithm,
            level1=request.level1,
            level2=request.level2,
            flagship_priority=request.flagship_priority,
            use_quick_repair=request.use_quick_repair,
        )

        controller = DecisiveController(ctx, config)
        results: list[dict[str, Any]] = []
        task_error: str | None = None

        try:
            for i in range(request.decisive_rounds):
                if task_manager.should_stop():
                    break

                task_manager.update_progress(current_round=i + 1, current_node='决战')
                _log.info('[Task] 决战第 {}/{} 轮', i + 1, request.decisive_rounds)
                result = controller.run()
                is_error = result.value == 'error'
                converted = {
                    'round': i + 1,
                    'success': not is_error,
                    'result': result.value,
                }
                if is_error:
                    task_error = '决战异常退出'
                    converted['error'] = task_error
                results.append(converted)
                task_manager.add_result(converted)

                if result.value in {'leave', 'error'}:
                    _log.warning('[Task] 决战第 {} 轮终止: {}', i + 1, result.value)
                    break
        except Exception as e:
            results.append({'round': len(results) + 1, 'success': False, 'error': str(e)})

        return TaskOutcome.from_results(results, error=task_error)

    return _start_task('decisive', request.decisive_rounds, executor)
