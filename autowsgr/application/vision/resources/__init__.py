"""Application-owned visual resources."""

from autowsgr.application.vision.resources.combat import CombatTemplates
from autowsgr.application.vision.resources.combat_keys import (
    RESULT_GRADE_KEYS,
    TemplateKey,
    get_templates,
)
from autowsgr.application.vision.resources.ops import Templates


__all__ = [
    'RESULT_GRADE_KEYS',
    'CombatTemplates',
    'TemplateKey',
    'Templates',
    'get_templates',
]
