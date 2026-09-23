"""验证 common.vision 的公共门面契约。"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from autowsgr.common import vision


def test_crop_and_transform() -> None:
    image = np.zeros((20, 30, 3), dtype=np.uint8)
    cropped = vision.crop(image, (0.2, 0.25, 0.6, 0.75))

    assert cropped.shape == (10, 12, 3)
    assert vision.transform(image, vision.ImageTransform.GRAY).shape == (20, 30)
    assert vision.transform(image, 'resize', size=(15, 10)).shape == (10, 15, 3)


def test_inspect_and_sample() -> None:
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    image[5, 5] = (10, 20, 30)
    color = vision.sample(image, 0.5, 0.5)
    signature = vision.PixelSignature(
        name='pixel',
        rules=(vision.PixelRule(0.5, 0.5, color),),
    )

    assert color == vision.Color(10, 20, 30)
    assert vision.inspect(image, signature).matched


def test_match_returns_unified_result() -> None:
    image = np.zeros((20, 30, 3), dtype=np.uint8)
    image[5:10, 8:14] = 255
    template = vision.ImageTemplate.from_ndarray(image[5:10, 8:14], name='sample')

    result = vision.match(image, template, confidence=0.99)

    assert result.matched
    assert result.best is not None
    assert result.best.template_name == 'sample'


def test_read_returns_text_and_number() -> None:
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    reader = SimpleNamespace(
        recognize=lambda _image, _allowlist: [
            SimpleNamespace(text='12K', confidence=0.9, bbox=(0, 0, 1, 1)),
        ],
    )

    result = vision.read(image, reader=reader, mode=vision.ReadMode.NUMBER)

    assert result.text == '12K'
    assert result.number == 12_000


def test_public_surface_hides_backends() -> None:
    assert not hasattr(vision, 'ImageChecker')
    assert not hasattr(vision, 'PixelChecker')
    assert not hasattr(vision, 'OCREngine')
