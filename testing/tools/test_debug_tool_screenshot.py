"""验证 debug toolkit 的截图产物保存。"""

from pathlib import Path

import cv2
import numpy as np

from tools.debug_toolkit.function.screenshot import save_image


def test_save_image_writes_rgb_png(tmp_path: Path) -> None:
    image = np.zeros((2, 3, 3), dtype=np.uint8)
    image[:, :] = (255, 0, 0)

    path = save_image(image, tag='sample', img_dir=tmp_path)

    assert path is not None
    saved = cv2.imread(str(path))
    assert saved is not None
    assert tuple(saved[0, 0]) == (0, 0, 255)
