"""Agent-facing entrypoint for the debug toolkit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == 'e2e':
        if __package__:
            from .function import e2e
        else:
            from tools.debug_toolkit.function import e2e

        return e2e.run(arguments[1:])

    if __package__:
        from .function import annotate, collect, inspect, ocr, roi, screenshot
    else:
        from tools.debug_toolkit.function import annotate, collect, inspect, ocr, roi, screenshot

    parser = argparse.ArgumentParser(prog='debug_toolkit')
    subparsers = parser.add_subparsers(dest='command', required=True)
    annotate.add_arguments(subparsers.add_parser('annotate'))
    screenshot.add_arguments(subparsers.add_parser('screenshot'))
    roi.add_arguments(subparsers.add_parser('roi'))
    ocr.add_arguments(subparsers.add_parser('ocr'))
    inspect.add_arguments(subparsers.add_parser('inspect'))
    collect.add_arguments(subparsers.add_parser('collect'))
    parser.epilog = 'e2e: debug_toolkit e2e <case arguments>'
    args = parser.parse_args(arguments)

    handlers = {
        'annotate': annotate.run,
        'collect': collect.run,
        'inspect': inspect.run,
        'ocr': ocr.run,
        'roi': roi.run,
        'screenshot': screenshot.run,
    }
    return handlers[args.command](args)


if __name__ == '__main__':
    raise SystemExit(main())
