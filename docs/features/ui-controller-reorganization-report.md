# UI Controller Reorganization Report

Date: 2026-09-06
Branch: `codex/20260830-sakuya-exercise-consolidated-7a6c`

## Scope

The page implementation tree moved from the legacy page package to
`autowsgr/application/ui/controller`. The old package was removed; no import
forwarding package was added.

## Final ownership

- `application/ui/controller`: page controllers and page-local workflow
  composition (`map`, `battle_preparation`, `decisive`, `event`, `mission_page`,
  `main_page`, and the standalone page controllers).
- `application/ui/controller/shared`: page-semantic capabilities shared by
  multiple controllers: `choose_ship.py` and `tabbed_page.py`.
- `application/ui/controller/battle_preparation/fleet_change`: shared by
  several combat flows, but kept beside the preparation base and detection
  mixins. Moving it under `shared` caused a real import cycle through
  `battle_preparation.__init__` and added no capability.
- `common/vision/blood.py`: shared blood-bar color classification used by
  preparation and combat result recognition.
- `common/vision/map.py`: map counter OCR and `LootShipCount`, used directly by
  sortie and campaign controllers.
- `common/calibration/map.py`: map coordinates, probes, colors, navigation
  timing values, and counter OCR crop regions.
- `battle_preparation/constants.py`: removed because it only re-exported
  values already owned by `common.calibration.battle_preparation`.

## Callers

Production modules, navigation graph/registry documentation, tests, tools,
examples, and feature documents now use `application.ui.controller`. Dynamic
patch targets were updated as well. A repository search found no remaining
legacy page-package reference outside ignored caches.

Navigation behavior was not changed. The navigation files differ from `HEAD`
only by page import paths and the Ruff-required ordering of the shared chooser
import in `registry.py`.

## Review findings addressed

Ponytail review confirmed the page/shared/common split and found one migration
regression: `shared/tabbed_page.py` still used the old `parents[3]` template
root. It now uses `parents[4]`, and all five tabbed templates load from
`autowsgr/common/data/images/ui`.

The map counter parser now declares `int | None` and checks for `None` before
normalizing an OCR result. A focused test covers a denominator-only result.

## Verification

- Canonical import smoke: passed, including navigation, page controllers,
  shared fleet/ship modules, and common vision modules.
- Template loading smoke: passed for map, build, intensify, mission, and friend.
- `tools/check_sortie_api.py`: passed.
- `python -m compileall -q autowsgr testing tools`: passed.
- Old package-path search: passed.
- Common-layer upper-import check: passed.
- `git diff --check`: passed.
- Scoped pre-commit (excluding four pre-existing dirty E2E tools): all hooks
  passed, including Ruff check/format and codespell.
- Focused pytest: `318 passed in 12.47s`.

## Residuals

The full changed-file pre-commit run still reports 16 inherited Ruff findings
in `tools/e2e_chapter_nav.py`, `tools/e2e/cases/bath_repair.py`,
`tools/e2e/cases/initialize.py`, and `tools/e2e/cases/reward.py`. This task only
changed their import paths, so their unrelated complexity and annotation
cleanup remains a separate task.

No real-device E2E or full pytest was run. The nine user-deleted historical
feature reports remain untouched.
