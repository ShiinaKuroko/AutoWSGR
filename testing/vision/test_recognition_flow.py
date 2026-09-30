"""公共视觉入口 recognition_flow 的最小契约测试。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy
import pytest

from autowsgr.common.vision.operations import recognition_flow as flow
from autowsgr.common.vision.operations.template_matching import ROI, Template


def _frame() -> numpy.ndarray:
    return numpy.zeros((4, 4, 3), dtype=numpy.uint8)


def _template(name: str = 't') -> Template:
    return Template(name=name, relative_path=f'{name}.png', image=_frame())


def _ctx() -> tuple[SimpleNamespace, MagicMock, MagicMock]:
    screenshots = MagicMock(side_effect=_frame)
    recorder = MagicMock()
    ctx = SimpleNamespace(
        runtime=SimpleNamespace(ctrl=SimpleNamespace(screenshot=screenshots)),
        record_screenshot=recorder,
    )
    return ctx, screenshots, recorder


def _match(matched: bool) -> SimpleNamespace:
    return SimpleNamespace(matched=matched, score=0.9 if matched else 0.1)


def _patch_sleep(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    sleep = MagicMock()
    monkeypatch.setattr(flow.time, 'sleep', sleep)
    return sleep


def test_shot_records_the_frame() -> None:
    ctx, screenshots, recorder = _ctx()

    frame = flow.shot(ctx)

    assert frame.shape == (4, 4, 3)
    screenshots.assert_called_once_with()
    recorder.assert_called_once_with(frame)


def test_before_template_hits_on_first_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, screenshots, _ = _ctx()
    monkeypatch.setattr(flow, 'match_template', lambda *_a, **_k: _match(True))

    result = flow.before_template(ctx, template=_template(), roi=ROI(0.0, 0.0, 1.0, 1.0))

    assert result.ok is True
    assert screenshots.call_count == 1


def test_before_template_retries_until_matched(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, screenshots, _ = _ctx()
    sleep = _patch_sleep(monkeypatch)
    outcomes = iter([_match(False), _match(True)])
    monkeypatch.setattr(flow, 'match_template', lambda *_a, **_k: next(outcomes))

    result = flow.before_template(ctx, template=_template(), attempts=3)

    assert result.ok is True
    assert screenshots.call_count == 2
    sleep.assert_called_once()


def test_before_template_reports_failure_after_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, screenshots, _ = _ctx()
    sleep = _patch_sleep(monkeypatch)
    monkeypatch.setattr(flow, 'match_template', lambda *_a, **_k: _match(False))

    result = flow.before_template(ctx, template=_template(), attempts=2)

    assert result.ok is False
    assert screenshots.call_count == 2
    sleep.assert_called_once()


def test_before_template_requires_expected_match_count(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _, _ = _ctx()
    templates = (_template('a'), _template('b'), _template('c'))
    outcomes = iter([_match(True), _match(True), _match(False)])
    monkeypatch.setattr(flow, 'match_template', lambda *_a, **_k: next(outcomes))

    unmet = flow.before_template(ctx, template=templates, attempts=1, min_matches=3)
    assert unmet.ok is False

    outcomes = iter([_match(True), _match(True), _match(False)])
    monkeypatch.setattr(flow, 'match_template', lambda *_a, **_k: next(outcomes))
    met = flow.before_template(ctx, template=templates, attempts=1, min_matches=2)
    assert met.ok is True


def test_single_template_rejects_other_match_counts() -> None:
    ctx, _, _ = _ctx()

    with pytest.raises(ValueError, match='min_matches'):
        flow.before_template(ctx, template=_template(), min_matches=2)


def test_after_template_waits_for_disappearance(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _, _ = _ctx()
    monkeypatch.setattr(flow, 'match_template', lambda *_a, **_k: _match(True))
    present = flow.after_template(ctx, template=_template(), attempts=1)
    assert present.ok is False

    monkeypatch.setattr(flow, 'match_template', lambda *_a, **_k: _match(False))
    gone = flow.after_template(ctx, template=_template(), attempts=1)
    assert gone.ok is True


def test_before_ocr_compares_expected_text(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _, _ = _ctx()
    detections = [SimpleNamespace(recognized_text='远征', confidence_score=0.99)]
    monkeypatch.setattr(flow, 'recognize_text', lambda *_a, **_k: detections)

    assert flow.before_ocr(ctx, expect='远征', attempts=1).ok is True
    assert flow.before_ocr(ctx, expect='演习', attempts=1).ok is False


def test_after_ocr_confirms_text_is_gone(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _, _ = _ctx()
    monkeypatch.setattr(flow, 'recognize_text', lambda *_a, **_k: [])

    assert flow.after_ocr(ctx, expect='远征', attempts=1).ok is True


def test_before_and_after_pixels_follow_the_match_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _, _ = _ctx()
    monkeypatch.setattr(flow, 'match_pixels', lambda *_a, **_k: SimpleNamespace(matched=True))

    assert flow.before_pixels(ctx, signature=object(), attempts=1).ok is True
    assert flow.after_pixels(ctx, signature=object(), attempts=1).ok is False
