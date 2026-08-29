"""后端命令行入口 — 将 YAML 任务提交给统一 Processor。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from autowsgr.dispatch import Processor, Request
from autowsgr.scheduler.launcher import Launcher


def build_parser() -> argparse.ArgumentParser:
    """创建 CLI 参数解析器。"""
    parser = argparse.ArgumentParser(prog='autowsgr')
    subparsers = parser.add_subparsers(dest='command', required=True)

    run = subparsers.add_parser('run', help='执行 YAML 任务')
    run.add_argument('yaml_path', type=Path)
    run.add_argument('--count', type=int, default=1, help='执行次数')
    run.add_argument('--extre', action='store_true', help='作为插队请求提交')
    run.add_argument('--config', type=Path, default=None, help='用户配置路径')

    exercise = subparsers.add_parser('exercise', help='执行演习 YAML 任务')
    exercise.add_argument('--yaml', dest='yaml_path', type=Path, required=True)
    exercise.add_argument('--count', type=int, default=1, help='执行次数')
    exercise.add_argument('--extre', action='store_true', help='作为插队请求提交')
    exercise.add_argument('--config', type=Path, default=None, help='用户配置路径')
    return parser


def main(argv: list[str] | None = None) -> int:
    """执行一个有限 YAML 请求并输出完成计数。"""
    args = build_parser().parse_args(argv)
    launcher = Launcher(args.config)
    processor: Processor | None = None
    try:
        request = Request.from_yaml(
            args.yaml_path,
            source='cli',
            count=args.count,
            extre=args.extre,
        )
        ctx = launcher.launch()
        processor = Processor(ctx)
        if request.extre:
            processor.interrupt(request)
        else:
            processor.submit(request)
        outcomes = processor.run_pending()
        completed = sum(1 for status, _request, _result in outcomes if status == 'done')
        failed = next(
            (str(result) for status, _request, result in outcomes if status == 'failed'), None
        )
        print(f'任务 {request.task_type}: count={completed}/{request.count}')  # noqa: T201
        if failed:
            print(f'任务失败: {failed}', file=sys.stderr)  # noqa: T201
            return 1
    except KeyboardInterrupt:
        if processor is not None:
            processor.stop()
        print('任务已中断', file=sys.stderr)  # noqa: T201
        return 130
    except Exception as exc:
        print(f'任务启动失败: {exc}', file=sys.stderr)  # noqa: T201
        return 1
    else:
        return 0 if completed == request.count else 2
    finally:
        launcher.disconnect()


if __name__ == '__main__':
    raise SystemExit(main())
