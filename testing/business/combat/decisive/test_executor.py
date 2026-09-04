"""决战业务入口回归。"""

from types import SimpleNamespace

import pytest

import autowsgr.business.combat.decisive.executor as executor_module
from autowsgr.business.combat.decisive import DecisiveExecutor, DecisiveResult
from autowsgr.dispatch.registry import build_executor


def test_decisive_is_registered_in_business_registry() -> None:
    """Processor registry resolves the business decisive executor."""
    executor = build_executor('decisive', SimpleNamespace(), {'chapter': 6})

    assert isinstance(executor, DecisiveExecutor)


def test_decisive_executor_delegates_one_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """The new entry delegates one task item to the migrated state machine."""

    class Controller:
        def __init__(self, _ctx: object, _config: object) -> None:
            pass

        def run(self) -> DecisiveResult:
            return DecisiveResult.CHAPTER_CLEAR

    monkeypatch.setattr(executor_module, 'DecisiveController', Controller)
    executor = DecisiveExecutor(SimpleNamespace(), {'chapter': 6})

    assert executor.run() is DecisiveResult.CHAPTER_CLEAR
