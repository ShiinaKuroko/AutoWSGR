"""模块功能：验证模板匹配结果自带归一化中心。

直接调用方：项目测试运行器。

直接依赖：NumPy、common.vision 的模板匹配适配层。

边界：只验证匹配结果中的中心字段，不涉及设备、页面和业务识别。
"""

from __future__ import annotations

import numpy as np

from autowsgr.common.vision.adapters.template_matching import Template, match_template


def _fixture() -> tuple[np.ndarray, Template]:
    """构造一块有纹理的画面和对应模板，模板落在 (4, 6)。"""
    rng = np.random.default_rng(20261010)
    pattern = rng.integers(0, 255, size=(2, 4, 3), dtype=np.uint8)
    screen = np.zeros((8, 10, 3), dtype=np.uint8)
    screen[6:8, 4:8] = pattern
    template = Template(
        name='probe',
        relative_path='probe.png',
        image=pattern,
        source_resolution=(10, 8),
    )
    return screen, template


def test_match_result_reports_normalized_template_center() -> None:
    """命中时中心指向模板在画面上的实际中心。"""
    screen, template = _fixture()

    result = match_template(screen, template, confidence=0.9)

    assert result.matched is True
    assert result.center == (0.6, 0.875)


def test_match_result_center_is_empty_when_not_matched() -> None:
    """未命中时中心为空值。"""
    screen, template = _fixture()
    blank = np.zeros_like(screen)

    result = match_template(blank, template, confidence=0.9)

    assert result.matched is False
    assert result.center is None
