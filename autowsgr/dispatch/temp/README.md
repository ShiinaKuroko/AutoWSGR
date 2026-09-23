# Vision temporary candidates

This directory is a quarantine area for reusable vision code found outside
`autowsgr/common/vision`. It is intended for the vision restructuring agent.

The files here are not imported by `autowsgr.common.vision`, are not part of
the production API, and must not be treated as the final module layout.

## Recovered candidates

| File | Source | Candidate capability |
| --- | --- | --- |
| `legacy_template_context.py` | `autowsgr/dispatch/image_context.py` | Request-local lazy template loading and caching. |

The old template matcher, pixel matcher, OCR engine, result models, and page
matching contracts were not copied from `common/vision`: they are the formal
vision rewrite currently being handled by another agent. No equivalent
implementation was found outside that layer.

## Deliberately excluded

Page templates and ROIs, ship-name normalization and fuzzy matching, combat,
damage, map, sortie, and native-DLL recognition remain application business
logic. Debug toolkit commands, screenshot writers, and test helpers remain
tooling or test logic. They are not common vision capabilities.

The generic OCR preprocessing and counter parsing candidates were promoted to
``opencv_engine.engine`` and ``ocr_engine.engine`` respectively.
