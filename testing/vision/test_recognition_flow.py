"""公共视觉入口的最小契约测试。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy
import pytest

from autowsgr.common.vision import (
    expect_ocr_absent,
    expect_pixels_absent,
    expect_template_absent,
    expect_ocr,
    expect_pixels,
    expect_template,
    service,
    shot,
)
from autowsgr.common.vision.adapters.template_matching import ROI, Template


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
    monkeypatch.setattr(service.time, 'sleep', sleep)
    return sleep


def test_shot_records_the_frame() -> None:
    ctx, screenshots, recorder = _ctx()

    frame = shot(ctx)

    assert frame.shape == (4, 4, 3)
    screenshots.assert_called_once_with()
    recorder.assert_called_once_with(frame)


def test_expect_template_hits_on_first_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, screenshots, _ = _ctx()
    monkeypatch.setattr(service, 'match_templates', lambda *_a, **_k: [_match(True)])

    result = expect_template(ctx, template=_template(), roi=ROI(0.0, 0.0, 1.0, 1.0))

    assert result.satisfied is True
    assert result.observation[0].matched is True
    assert result.screenshot.shape == (4, 4, 3)
    assert screenshots.call_count == 1


def test_expect_template_retries_until_matched(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, screenshots, _ = _ctx()
    sleep = _patch_sleep(monkeypatch)
    outcomes = iter([[_match(False)], [_match(True)]])
    monkeypatch.setattr(service, 'match_templates', lambda *_a, **_k: next(outcomes))

    result = expect_template(ctx, template=_template(), attempts=3)

    assert result.satisfied is True
    assert screenshots.call_count == 2
    sleep.assert_called_once()


def test_expect_template_reports_failure_after_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, screenshots, _ = _ctx()
    sleep = _patch_sleep(monkeypatch)
    monkeypatch.setattr(service, 'match_templates', lambda *_a, **_k: [_match(False)])

    result = expect_template(ctx, template=_template(), attempts=2)

    assert result.satisfied is False
    assert screenshots.call_count == 2
    sleep.assert_called_once()


def test_expect_template_requires_expected_match_count(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _, _ = _ctx()
    templates = (_template('a'), _template('b'), _template('c'))
    outcomes = iter([[_match(True), _match(True), _match(False)]])
    monkeypatch.setattr(service, 'match_templates', lambda *_a, **_k: next(outcomes))

    unmet = expect_template(ctx, template=templates, attempts=1, min_matches=3)
    assert unmet.satisfied is False

    outcomes = iter([[_match(True), _match(True), _match(False)]])
    monkeypatch.setattr(service, 'match_templates', lambda *_a, **_k: next(outcomes))
    met = expect_template(ctx, template=templates, attempts=1, min_matches=2)
    assert met.satisfied is True


def test_template_rejects_non_positive_match_count() -> None:
    ctx, _, _ = _ctx()

    with pytest.raises(ValueError, match='min_matches'):
        expect_template(ctx, template=_template(), min_matches=0)


def test_expect_template_absent_waits_for_disappearance(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _, _ = _ctx()
    monkeypatch.setattr(service, 'match_templates', lambda *_a, **_k: [_match(True)])
    present = expect_template_absent(ctx, template=_template(), attempts=1)
    assert present.satisfied is False

    monkeypatch.setattr(service, 'match_templates', lambda *_a, **_k: [_match(False)])
    gone = expect_template_absent(ctx, template=_template(), attempts=1)
    assert gone.satisfied is True


def test_expect_ocr_compares_expected_text(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _, _ = _ctx()
    detections = [SimpleNamespace(recognized_text='远征', confidence_score=0.99)]
    monkeypatch.setattr(service, 'recognize_text', lambda *_a, **_k: detections)

    assert expect_ocr(ctx, expect='远征', attempts=1).satisfied is True
    assert expect_ocr(ctx, expect='演习', attempts=1).satisfied is False


def test_expect_ocr_absent_confirms_text_is_gone(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _, _ = _ctx()
    monkeypatch.setattr(service, 'recognize_text', lambda *_a, **_k: [])

    assert expect_ocr_absent(ctx, expect='远征', attempts=1).satisfied is True


def test_before_and_expect_pixels_absent_follow_the_match_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _, _ = _ctx()
    monkeypatch.setattr(service, 'match_pixels', lambda *_a, **_k: SimpleNamespace(matched=True))

    assert expect_pixels(ctx, signature=object(), attempts=1).satisfied is True
    assert expect_pixels_absent(ctx, signature=object(), attempts=1).satisfied is False
